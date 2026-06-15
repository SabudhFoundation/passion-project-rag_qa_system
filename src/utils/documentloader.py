from docling.document_converter import DocumentConverter,PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
import pandas as pd
import fitz
import logging
import gc
import time
import docling
import psutil
import re
import string
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger(__name__)

SUPPORTED_FORMATS={"csv","pdf","txt"}
MIN_TEXT_LENGTH=100
DEFAULT_BATCH_SIZE=1
class DocumentNotSupportedError(Exception):
    pass
class FileNotLoaded(Exception):
    pass

class DocumentLoader:

    def __init__(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True      # saves significant memory
        pipeline_options.do_picture_classification = False
        pipeline_options.do_picture_description = False
        pipeline_options.do_chart_extraction = False
        pipeline_options.images_scale = 0.5
        pipeline_options.generate_page_images = False
        pipeline_options.generate_picture_images = False
        pipeline_options.generate_table_images = False
        pipeline_options.ocr_batch_size = 1   # ✅ 1 page at a time through OCR model
        pipeline_options.layout_batch_size = 1 

        self.ocr_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    def load(self,file_path:str) -> str:
        file_type=file_path.rsplit('.',1)[-1].lower()
        if file_type not in SUPPORTED_FORMATS:
            raise DocumentNotSupportedError(
            f"Unsupported Foramt: {file_type}\n"
            f"Supported Format: {SUPPORTED_FORMATS}"
            )
        loaders={
            "pdf":self.pdf_loader,
            "csv":self.csv_loader,
            "txt":self.txt_loader
        }
        try:
            result=loaders[file_type](file_path)
            result["File_Type"]=file_type
            result["File_Path"]=file_path
            return result
        except Exception as e :
            raise FileNotLoaded(f"Failed to load your file: {e}!\nTry again!")



    def pdf_loader(self, file_path: str) -> str:
        try:
            print("Fast Extraction path")
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False

            converter = DocumentConverter(
            format_options={
            InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
            backend=PyPdfiumDocumentBackend
                )
             }
            )
            result = converter.convert(file_path)
            text = self.text_extractor(result)
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
            extracted_pages = len(result.document.pages)
            logger.info(
            "PDF pages: %d | Extracted pages: %d",
            total_pages,
            extracted_pages
            )
            if extracted_pages < total_pages:
                logger.warning("Some pages missing in fast extraction!")
                raise DocumentNotSupportedError("Scanned PDFs are not supported.")
            if self.needs_ocr(text):
                raise DocumentNotSupportedError("Scanned PDFs are not supported.")
            logger.info("Docling fast extraction succeeded.")
            return {                                               # ← return dict like txt and csv
            "Text": text,
            "Document": result.document,
            "Is_OCR_Fallback": False
            }
        except DocumentNotSupportedError:
            logger.warning("Scanned PDF detected, falling back to OCR...")
            return self.ocr_pdf_loader(file_path)
        except Exception as e:
            logger.warning("Fast PDF Extraction Failed! %s", e)
            raise FileNotLoaded(f"Failed to load PDF: {e}")

    def ocr_pdf_loader(self, file_path: str) -> dict:
        try:
            logger.info("OCR extraction path")
            result = self.ocr_converter.convert(file_path)
            text = self.text_extractor(result)

            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()

            extracted_pages = len(result.document.pages)
            logger.info(
                "PDF pages: %d | Extracted pages: %d",
                total_pages,
                extracted_pages
            )

            if extracted_pages < total_pages:
                logger.warning("Some pages missing even after OCR!")

            logger.info("OCR extraction succeeded.")
            return {
                "Text": text,
                "Document": result.document,
                "Is_OCR_Fallback": True          # ← only difference from pdf_loader
            }

        except Exception as e:
            logger.warning("OCR PDF Extraction Failed! %s", e)
            raise FileNotLoaded(f"Failed to load PDF with OCR: {e}")
    
    def batched_ocr_loader(self,file_path:str,batch_size:int=DEFAULT_BATCH_SIZE) -> str:
        doc=fitz.open(file_path) #fitz is import name for PyMUPDF
        total_pages=len(doc)
        doc.close()

        all_text:list[str]=[]
        page_index=0
        while page_index < total_pages:
            batch_end=min(page_index+batch_size,total_pages)
            page_range=list(range(page_index,batch_end))
            
            chunk=self.ocr_page_range(file_path,page_range)

            if chunk is None and batch_size>1:
                logger.warning("The batch upon which OCR is applied is getiing out of memory error\nRetrying page by page %s",page_range)
                for single in page_range:
                    single_chunk=self.ocr_page_range(file_path,[single])
                    if single_chunk:
                        all_text.append(single_chunk)
                    else:
                        logger.error("Page even failed ocr inspite of singel chunking %s",single)
            elif chunk:
                all_text.append(chunk)

            page_index=batch_end
            gc.collect() #calling garbage collector and releasing memory between batches
            time.sleep(1)
        
        if not all_text:
            raise FileNotLoaded("OCR produced no text for the document")
        
        return {"Text":"\n\n".join(all_text),"Document":None,"Is_OCR_Fallback": True}
                        

    def ocr_page_range(self,file_path:str,pages:list[int]) -> str|None:
        retries=2
        for attempts in range(retries):
            try:
                print(f"Processing pages {pages}, attempt {attempts + 1}")
                print("Processing Your Document!\nWait....")
                available_ram = psutil.virtual_memory().available / (1024 ** 3)
                if available_ram < 0.3:  # if less than 1GB free
                    logger.warning("Low RAM! Only %.1fGB free", available_ram)
                    gc.collect()         # clean up memory
                    time.sleep(5 ** attempts)  # wait before retrying 
                page_range = (min(pages) + 1, max(pages) + 1)
                ocr_result=self.ocr_converter.convert(file_path,page_range=page_range)
                ocr_output=" ".join([t.text for t in ocr_result.document.texts if t.text.strip()])
                return ocr_output

            except Exception as e:
                logger.warning("Attempt %d failed: %s", attempts + 1, e)
                gc.collect()
                time.sleep(5 ** attempts)

        logger.error("All attempts failed for pages %s, skipping", pages)
        return None 

    @staticmethod
    def text_extractor(result: object) -> str:

        pages_output = []

        for page_no, page in result.document.pages.items():

            page_texts = []

            for item in result.document.texts:

                if hasattr(item, "prov") and item.prov:

                    for prov in item.prov:

                        if prov.page_no == page_no:

                            if item.text.strip():
                                page_texts.append(item.text)

                            break
        
            page_content = "\n".join(page_texts).strip()

            pages_output.append(f"\n\n========== PAGE {page_no} ==========\n\n{page_content}")

        return "\n".join(pages_output)


    @staticmethod
    def needs_ocr(text:str) -> bool:
        stripped=text.strip()
        if not stripped:
            return True
        if len(stripped)<MIN_TEXT_LENGTH:
            return True
        printable = sum(c in string.printable for c in text)
        printable_ratio = printable / max(len(text), 1)

    # alphabetic ratio
        alpha = sum(c.isalpha() for c in text)
        alpha_ratio = alpha / max(len(text), 1)

    # weird unicode symbols
        weird = len(re.findall(r'[^\w\s.,!?;:\-()\'"]', text))
        weird_ratio = weird / max(len(text), 1)

        print(f"Printable Ratio: {printable_ratio:.2f}")
        print(f"Alpha Ratio: {alpha_ratio:.2f}")
        print(f"Weird Ratio: {weird_ratio:.2f}")
        if printable_ratio < 0.7:
            return True

        if alpha_ratio < 0.3:
            return True

        if weird_ratio > 0.3:
            return True
    
        return False
       



    def txt_loader(self,file_path):
        converter=DocumentConverter(allowed_formats=[InputFormat.TXT])
        result=converter.convert(file_path)
        output=" ".join([t.text for t in result.document.texts])
        return {
                "Text":output,
                "Document":result.document,
                "Is_OCR_Fallback":False
                }
    
    def csv_loader(self,file_path:str) -> str:
        try:
            csv_result = DocumentConverter().convert(source=file_path)
            csv_doc = csv_result.document
            markdown_text = csv_doc.export_to_markdown()
            
        except Exception as e:
            raise FileNotLoaded(f"CSV File not loaded {file_path}")
        return {
            "Document": csv_doc,
            "Text": markdown_text,
            "Num_Tables": len(csv_doc.tables),
            "Num_Rows": csv_doc.tables[0].data.num_rows if csv_doc.tables else 0,
            "Num_Columns": csv_doc.tables[0].data.num_cols if csv_doc.tables else 0
        }
        
'''
if __name__ == "__main__":
    loader = DocumentLoader()
    file_path =r"E:\ElectricCarDataset\ElectricCarData_Clean.csv"   
    output = loader.load(file_path)
    #print("LENGTH:", len(output["Text"]))
    doc = output["Document"]
"""
    print("\n========== BASIC INFO ==========")
    print("Tables:", len(doc.tables))
    print("Texts:", len(doc.texts))
    print("Pages:", len(doc.pages))

    print("\n========== MARKDOWN PREVIEW ==========")
    print(doc.export_to_markdown()[:30])
"""
headers=[]
first_table=doc.tables[0]
headers=[cell.text.strip() for cell in first_table.data.table_cells if cell.column_header]
for header in headers:
    print(header)
    for i, table in enumerate(doc.tables):
        print(f"\n--- TABLE {i} ---")

        print("Rows:", table.data.num_rows)
        print("Columns:", table.data.num_cols)

        print("\nFirst 5 cells:")

        for cell in table.data.table_cells[:5]:

            print({"text": cell.text,"row": cell.start_row_offset_idx,"col": cell.start_col_offset_idx})
'''
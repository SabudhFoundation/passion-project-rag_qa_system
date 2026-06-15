import uuid

class ChunkerError(Exception):
    pass


class HotpotChunker:

    def chunking(self, table2_json: list[dict]) -> list[dict]:

        try:

            chunks = []

            print("Chunking started!")

            for item in table2_json:

                title = item["label"]

                # context is full joined string currently
                # so split back into sentences
                sentences = item["context"]

                # if already list keep it
                if isinstance(sentences, str):
                    sentences = sentences.split(".")

                for sen_index, sentence in enumerate(sentences):

                    sentence = sentence.strip()

                    if not sentence:
                        continue

                    chunk = {

                        "chunk_id": str(uuid.uuid4()),

                        "text": title + "\n\n" + sentence,

                        "metadata": {

                            "label": title,
                            "label_id": item["_id"], 
                            "sen_index": sen_index

                        }
                    }

                    chunks.append(chunk)

            print(
                "Chunking ended!\nLength of chunks:",
                len(chunks)
            )

            return chunks

        except Exception as e:

            raise ChunkerError(
                f"Error in chunking {e}"
            )
import uuid
class ExtractingFieldError(Exception):
    pass


class ExtractingField:

    def extracting_fields(self, data: list[dict]):

        try:
            
            table1=[] #will store question along with _id,followed by supporting facts 
            table2=[] #will store context used to answer these questions
            seen_labels=set()
            label_dict={}
            for index,json_dict in enumerate(data):
                if not json_dict:
                    continue
                #---building table 2 ---
                context=json_dict["context"]
                for context_data in context:
                    label,ctx_data=context_data[0],context_data[1]
                    if label not in seen_labels:
                        seen_labels.add(label)  
                        table_data={
                            "_id":str(uuid.uuid4()),
                            "label":label,
                            "context":ctx_data
                        }    
                        table2.append(table_data)  
                        label_dict[label]=table_data["_id"]
                        
                #---Build table 1---
                question=json_dict["question"]
                question_id=json_dict["_id"]
                supporting_facts=json_dict["supporting_facts"]
                supporting_facts_list = []
                for sf in supporting_facts:
                    label,sf_index=sf[0],sf[1]
                    if label in label_dict:
                        supporting_facts_list.append({
                            "label_id": label_dict[label],
                            "sentence_index": sf_index  # ✅ renamed: it's a sentence index, not context index
                        })
                table1.append({
                    "_id": question_id,
                    "question": question,
                    "supporting_facts": supporting_facts_list,
                })

            return table1,table2
        
        except Exception as e:

            raise ExtractingFieldError(
                f"Error in Extracting Fields {e}"
            )
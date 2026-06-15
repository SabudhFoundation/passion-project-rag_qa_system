import json
class HotpotDatasetLoadingError(Exception):
    pass

class HotpotLoader:
    def loader_hotpot(self,file_path:str) -> list[dict]:
        try:
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    print(data[:2])
                    return data
        except Exception as e:
            raise HotpotDatasetLoadingError(f"Dataset not loaded: {e}")

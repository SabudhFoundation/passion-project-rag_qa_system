
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import os
import json
import gc
from transformers.utils import logging

logging.set_verbosity_info()

EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
CHECKPOINT_DIR = "embedding_checkpoints"


class EmbeddingError(Exception):
    pass


class Embedder:
    def __init__(self):
        print(EMBED_MODEL_ID)
        self.model = SentenceTransformer(
            EMBED_MODEL_ID,
            device="cpu"
        )
        print("model loaded")

    def generate_embeddings(
        self,
        chunks: List[dict],
        batch_size: int = 1024,                          # reduced from 256 to avoid OOM
        checkpoint_every: int = 10                     # save every 10 batches
    ) -> list[dict]:

        if not chunks:
            return []

        os.makedirs(CHECKPOINT_DIR, exist_ok=True)
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "results_checkpoint.json")
        meta_file = os.path.join(CHECKPOINT_DIR, "meta.json")

        # ── Load existing progress ──────────────────────────────────────────
        completed_count = 0
        results = []

        if os.path.exists(checkpoint_file) and os.path.exists(meta_file):
            print("Found checkpoint! Resuming...")
            with open(meta_file, "r") as f:
                meta = json.load(f)
            completed_count = meta.get("completed_count", 0)

            with open(checkpoint_file, "r") as f:
                results = json.load(f)

            print(f"Resuming from chunk {completed_count} / {len(chunks)}")
        else:
            print("No checkpoint found. Starting fresh.")

        # ── Filter and slice remaining work ────────────────────────────────
        filtered = [c for c in chunks if c.get("text", "").strip()]

        if completed_count >= len(filtered):
            print("All chunks already embedded!")
            return results

        remaining = filtered[completed_count:]

        print("Generation Started")

        try:
            for batch_idx, i in enumerate(range(0, len(remaining), batch_size)):
                batch = remaining[i: i + batch_size]
                texts = [c["text"] for c in batch]

                vectors = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )

                for chunk, vector in zip(batch, vectors):
                    results.append({
                        "chunk_id": chunk["chunk_id"],
                        "embedding": vector.tolist()
                            if isinstance(vector, np.ndarray)
                            else list(vector),
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    })

                completed_count += len(batch)

                # progress log
                total_batches = (len(remaining) + batch_size - 1) // batch_size
                print(f"Batch {batch_idx + 1}/{total_batches} done  |  Chunks: {completed_count}/{len(filtered)}")

                # ── Save checkpoint every N batches ────────────────────────
                if (batch_idx + 1) % checkpoint_every == 0:
                    self._save_checkpoint(results, completed_count, checkpoint_file, meta_file)

                # free memory
                gc.collect()

        except Exception as e:
            # save whatever we have before crashing
            print("Error occurred — saving checkpoint before exit...")
            self._save_checkpoint(results, completed_count, checkpoint_file, meta_file)
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")

        # ── All done — clean up checkpoints ────────────────────────────────
        print("Generation ended")
        self._save_checkpoint(results, completed_count, checkpoint_file, meta_file)  # final save
        print(f"Removing checkpoints...")
        os.remove(checkpoint_file)
        os.remove(meta_file)

        print("Results returned")
        return results

    # ── Helper ───────────────────────────────────────────────────────────────
    def _save_checkpoint(self, results, completed_count, checkpoint_file, meta_file):
        with open(checkpoint_file, "w") as f:
            json.dump(results, f)
        with open(meta_file, "w") as f:
            json.dump({"completed_count": completed_count}, f)
        print(f"Checkpoint saved ({completed_count} chunks done)")
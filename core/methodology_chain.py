"""
MethodologyChain - Separate RAG vectorstore for trainer methodology patterns

Keeps methodology knowledge separate from theory/anatomy RAG (knowledge_chain.py).
Fed by PatternExtractor from imported cards.

Usage:
    chain = MethodologyChain()
    chain.add_card_to_rag(card_id, parsed_card, patterns)
    context = chain.retrieve_style_context(goal="hypertrophy", level="intermediate")
"""

import json
from typing import Optional, Dict, Any, List

from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from core.config import METHODOLOGY_VECTORSTORE_DIR, EMBEDDING_MODEL
from core.card_parser import ParsedCard
from core.error_handler import logger


class MethodologyChain:
    """Separate vectorstore for trainer methodology patterns."""

    def __init__(self):
        self.vectorstore = None
        self.retriever = None
        self._initialize()

    def _initialize(self):
        """Load or create the methodology vectorstore."""
        try:
            embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
            persist_dir = str(METHODOLOGY_VECTORSTORE_DIR)

            # Load existing or create empty vectorstore
            self.vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings,
                collection_name="trainer_methodology",
            )
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            logger.info("MethodologyChain: vectorstore loaded")
        except Exception as e:
            logger.warning(f"MethodologyChain: init failed ({e})")
            self.vectorstore = None
            self.retriever = None

    def add_card_to_rag(
        self,
        card_id: int,
        parsed_card: ParsedCard,
        patterns: Dict[str, Any]
    ) -> bool:
        """
        Add a card's extracted patterns to the methodology vectorstore.

        Creates a Document with pattern summary as content and
        card metadata (goal, split, card_id) for filtering.
        """
        if self.vectorstore is None:
            logger.warning("MethodologyChain: vectorstore not available")
            return False

        try:
            # Build document content from patterns
            content_parts = []

            preferred = patterns.get("preferred_compound_exercises", [])
            if preferred:
                content_parts.append(f"Esercizi preferiti: {', '.join(preferred)}")

            set_scheme = patterns.get("set_scheme")
            if set_scheme:
                content_parts.append(f"Schema serie/reps: {set_scheme}")

            philosophy = patterns.get("accessory_philosophy")
            if philosophy:
                content_parts.append(f"Filosofia accessori: {philosophy}")

            ordering = patterns.get("ordering_style")
            if ordering:
                content_parts.append(f"Ordine esercizi: {ordering}")

            progression = patterns.get("progression_style")
            if progression:
                content_parts.append(f"Progressione: {progression}")

            notes = patterns.get("notes_for_ai")
            if notes:
                content_parts.append(f"Note stile: {notes}")

            # Add exercise list summary
            if parsed_card.exercises:
                ex_names = [ex.name for ex in parsed_card.exercises[:10]]
                content_parts.append(f"Esercizi nella scheda: {', '.join(ex_names)}")

            if not content_parts:
                return False

            content = "\n".join(content_parts)

            # Metadata for filtering
            metadata = {
                "card_id": card_id,
                "goal": parsed_card.metadata.detected_goal or "generic",
                "split": parsed_card.metadata.detected_split or "generic",
                "source": "imported_card",
            }

            doc = Document(page_content=content, metadata=metadata)
            self.vectorstore.add_documents([doc])
            logger.info(f"MethodologyChain: added card {card_id} to vectorstore")
            return True

        except Exception as e:
            logger.error(f"MethodologyChain: add_card_to_rag failed: {e}")
            return False

    def retrieve_style_context(
        self,
        goal: str = "generic",
        level: str = "intermediate",
        split: Optional[str] = None
    ) -> str:
        """
        Query the methodology vectorstore for relevant style context.

        Returns concatenated text from most relevant methodology documents.
        """
        if self.retriever is None:
            return ""

        try:
            query = f"Stile allenamento per {goal} livello {level}"
            if split:
                query += f" con split {split}"

            docs = self.retriever.invoke(query)

            if not docs:
                return ""

            # Concatenate document contents
            context_parts = []
            for doc in docs:
                context_parts.append(doc.page_content)

            return "\n---\n".join(context_parts)

        except Exception as e:
            logger.warning(f"MethodologyChain: retrieve failed: {e}")
            return ""

    def get_status(self) -> Dict[str, Any]:
        """Return vectorstore status."""
        if self.vectorstore is None:
            return {"available": False, "documents_count": 0}

        try:
            collection = self.vectorstore._collection
            count = collection.count()
            return {"available": True, "documents_count": count}
        except Exception:
            return {"available": True, "documents_count": 0}

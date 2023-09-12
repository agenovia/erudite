import logging
import multiprocessing as mp
from typing import List, Union

from weaviate import Client as WeaviateClient
from weaviate.batch import Batch as WeaviateBatch

from .types import Batch, Entry, Reference

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")


class WeaviateImporter:
    """
    Base class for importing data objects in the form of a single Entry or
    a Collection of Entry to Weaviate. Automatically handles the linking
    of references if an Entry has a Reference attached to it.
    """

    def __init__(self, client: WeaviateClient, data_object: Union[Entry, Batch]):
        self.client = client
        self.data_object = data_object
        self.logger = logging.getLogger()
        self.pool = mp.Pool(mp.cpu_count())

    def callback_log(self, message, level="info"):
        if level == "info":
            logging.info(message)
        elif level == "error":
            logging.error(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "debug":
            logging.debug(message)

    def load_batch(self):
        """Iterates over a Batch and load the contained Entry"""
        assert isinstance(
            self.data_object, Batch
        ), f"{self.data_object} is not a Collection object."
        for entry in self.data_object.get_entries():
            self.load_entry(entry)
            # self.pool.apply_async(self.load_entry, args=(entry,), callback=self.callback_log)

    def load_entry(self, entry):
        """Loads a single Entry to Weaviate.

        Also automatically links other entries if a Reference is attached.
        """
        batch = self.client.batch
        try:
            assert isinstance(entry, Entry), f"{entry} is not an Entry object."
            logger.info("Inserting %s", entry)
            batch.add_data_object(
                class_name=entry.class_name, data_object=entry.entry, uuid=entry.uuid
            )
            self.resolve_references(batch, entry.get_references())
        except AssertionError as exc:
            logging.error(exc, exc_info=True)
        finally:
            batch.flush()
        return ("%s inserted", self)

    def resolve_references(self, batch: WeaviateBatch, references: List[Reference]):
        """Resolves all references"""
        for ref in references:
            batch.add_reference(
                from_object_class_name=ref.parent.class_name,
                to_object_class_name=ref.child.class_name,
                from_object_uuid=ref.parent.uuid,
                to_object_uuid=ref.child.uuid,
                from_property_name=ref.on_parent_property,
            )
            if ref.on_child_property:
                # this reference is a two-way reference and the
                # child has its own reference to its parent
                batch.add_reference(
                    from_object_class_name=ref.child.class_name,
                    to_object_class_name=ref.parent.class_name,
                    from_object_uuid=ref.child.uuid,
                    to_object_uuid=ref.parent.uuid,
                    from_property_name=ref.on_child_property,
                )

    def run(self):
        """Load the Entry or Collection into Weaviate using the provided Client."""
        # is the data passed a single entry or a collection of entries
        logging.info("run")
        if isinstance(self.data_object, Batch):
            self.load_batch()
        elif isinstance(self.data_object, Entry):
            self.load_entry(self.data_object)

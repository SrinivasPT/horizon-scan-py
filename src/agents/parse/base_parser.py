import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from aiohttp import ClientSession

from model.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseParser(ABC):

    def __init__(self, session: ClientSession):
        self.session = session

    @abstractmethod
    async def parse(self, content: str, config: Dict, base_url: str) -> List[Document]:
        pass

import math
import requests
import time
import os
import numpy as np

from hashlib import blake2b
from io import BytesIO
from PIL import Image as PILImage
from threading import Thread, Lock

from . import palette_from_image, camel_to_snake
from .palettes import Color

SEARCH_CACHE = {}
IMAGE_CACHE = {}


class Image:
    def __init__(self, n=5, **kwargs):
        for k, v in kwargs.items():
            setattr(self, camel_to_snake(k), v)

        self.preview = self.load_preview()

        if self.preview:
            self.palette = palette_from_image(self.preview, n)
            self.palette = Color.batch(self.palette, format_in="rgb")

    def __str__(self):
        return str(self.id)

    @property
    def json(self):
        return {
            "id": self.id,
            "preview_url": self.webformat_url,
            "image_url": self.large_image_url,
        }

    def load_preview(self):
        if not hasattr(self, "preview_url"):
            return None

        # Load remote image, convert to bytes stream and open as PIL Image
        res = requests.get(self.preview_url, stream=True)
        io = BytesIO(res.raw.read())
        return PILImage.open(io)


class MoodSearch:
    def __init__(self, id, query, palette):
        self.id = id

        self.query = query
        self.palette = Color.batch(palette)
        self.n = len(self.palette)

        self.status = "initialized"

        self.hits = self.load_page(page_size=5)["totalHits"]
        self.progress = 0
        self.images = []
        self.main_thread = None

        self.perform()

    @classmethod
    def search_id(self, query, palette):
        """Generate ID unique to query string and palette"""
        return blake2b(
            f"{query.lower()}.{','.join(palette)}".encode(), digest_size=16
        ).hexdigest()

    def load_page(self, page_number=1, page_size=100):
        """Get search results from pixabay"""
        url = "https://pixabay.com/api/"
        params = {
            "key": os.environ.get("PIXABAY_API_KEY", ""),
            "q": self.query,
            "image_type": "photo",
            "per_page": page_size,
            "page": page_number,
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            self.status = "error"

        return response.json()

    def thread_load_image(self, image):
        """Load single image asynchronously"""
        img = get_image(n=self.n, **image)

        # Lock to edit self.images
        self.lock.acquire()
        self.images.append(img)
        self.progress += 1

        # Unlock
        self.lock.release()

    def thread_load_all(self):
        """Load all available pages asynchronously"""
        start_time = time.time()

        self.lock = Lock()
        self.threads = []

        # Calculate how many iterations with page_size 100
        for i in range(math.ceil(self.hits / 100)):
            res = self.load_page(i + 1)
            for hit in res["hits"]:
                t = Thread(target=MoodSearch.thread_load_image, args=(self, hit))
                t.start()
                self.threads.append(t)

        # Status: not done yet, timeout after 60 seconds, refresh every second
        while self.progress != self.hits and time.time() - start_time < 60:
            time.sleep(1)

        # Status: done
        self.status = "done"
        self.ranked_images = self.rank()

    def perform(self):
        """Perform the asynchronous search"""
        self.status = "fetching_data"
        self.main_thread = Thread(target=MoodSearch.thread_load_all, args=(self,))
        self.main_thread.start()

    def sort_key(self, x):
        # Sort based on euclidean distance between palette of input and image
        return np.linalg.norm(
            np.array(list(map(lambda y: y.out("rgb"), x.palette)))
            - np.array(list(map(lambda y: y.out("rgb"), self.palette))),
        )

    def rank(self):
        return sorted(self.images, key=self.sort_key)


def get_image(**kwargs):
    """Load image from cache or create new"""
    image_id = kwargs.get("id")
    if image_id is None:
        return None

    if image_id not in IMAGE_CACHE:
        IMAGE_CACHE[image_id] = Image(**kwargs)

    return IMAGE_CACHE[image_id]


def get_search(search_id=None, query=None, palette=None):
    """Load search from cache or create new"""
    if not search_id and not any([query, palette]):
        raise ValueError("either search_id or query and palette need to be set")

    if not search_id:
        search_id = MoodSearch.search_id(query, palette)

    if search_id not in SEARCH_CACHE:
        SEARCH_CACHE[search_id] = MoodSearch(search_id, query, palette)

    return SEARCH_CACHE[search_id]
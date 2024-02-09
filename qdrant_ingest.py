import numpy as np
import pandas as pd
from config import settings
from qdrant_client import QdrantClient, grpc
from tqdm import tqdm
from qdrant_client.http.models import Distance, VectorParams
"""
A class for ingesting data into Qdrant.

Attributes:
    client_grpc (QdrantClient): A client for interacting with Qdrant.

    item_path (numpy.ndarray): Array of item URLs.
    item_image (numpy.ndarray): Array of item images.
    item_name (numpy.ndarray): Array of item names.
    fixed_item_price (numpy.ndarray): Array of item prices.
    sale_item_price (numpy.ndarray): Array of sale item prices.
    sales_number (numpy.ndarray): Array of sales numbers.
    shop_path (numpy.ndarray): Array of shop paths.
    shop_name (numpy.ndarray): Array of shop names.
    image_features (numpy.ndarray): Array of features to be ingested.
"""
class QdrantIngest:
    def __init__(self):
        # Create a client to interact with Qdrant
        self.client_grpc = QdrantClient(url=settings.QDRANT_URL, prefer_grpc=True)

        data = pd.read_csv(settings.DATA_PATH)
        # Extract attributes from the dataset
        self.item_path = data["item_path"]
        self.item_image = data["item_image"]
        self.item_name = data["item_name"]
        self.fixed_item_price = data["fixed_item_price"]
        self.sale_item_price = data["sale_item_price"]
        self.sales_number = data["sales_number"]
        self.shop_path = data["shop_path"]
        self.shop_name = data["shop_name"]
        # Load array features
        self.image_features = np.load(settings.FEATURES_PATH, allow_pickle=True)

    def create_collection(self):
        response = self.client_grpc.grpc_collections.Create(
            grpc.CreateCollection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=grpc.VectorsConfig(
                    params=grpc.VectorParams(
                        size=settings.DIMENSIONS,
                        distance=grpc.Distance.Cosine,
                    )
                ),
                timeout=10,
            )
        )
        return response
    
    def check_collection(self):
        response = self.client_grpc.grpc_collections.Get(
            grpc.GetCollectionInfoRequest(collection_name=settings.QDRANT_COLLECTION)
        )
        return response

    def add_points(self,batch_size=1000):
        '''
        Adds data points to the Qdrant collection
        '''
        num_features = self.image_features["image_features"].shape[0]
        # num_features = 2000
        num_batches = (num_features + batch_size - 1) // batch_size

        for i in tqdm(range(num_batches)):
            # Split into batches
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, num_features)

            ids = list(range(start_idx, end_idx))

            payloads = [
                {
                    "item_path": self.item_path[idx],
                    "item_image": self.item_image[idx],
                    "item_name": self.item_name[idx],
                    "fixed_item_price": int(self.fixed_item_price[idx]),
                    "sale_item_price": int(self.sale_item_price[idx]),
                    "sale_rate": float(
                        1 - self.sale_item_price[idx] / self.fixed_item_price[idx]
                    ),
                    "sales_number": int(self.sales_number[idx]),
                    "shop_path": self.shop_path[idx],
                    "shop_name": self.shop_name[idx],
                }
                for idx in range(start_idx, end_idx)
            ]

            vectors = self.image_features["image_features"][start_idx:end_idx]

            self.client_grpc.upload_collection(
                collection_name= settings.QDRANT_COLLECTION,
                vectors=vectors,
                payload=payloads,
                ids=ids
            )
        print("Done adding points to the collection!")

def main():
    """
    Main function to perform QdrantIngest data ingestion.
    """
    qdrant_ingest = QdrantIngest()

    try:
        response = qdrant_ingest.check_collection()
        if response.result.status == 1:
            print("Collection already exists!")
    except Exception as e:
        print(f"Error checking collection: {e}")

        print("Create collection!")
        response = qdrant_ingest.create_collection()
        print(response)
        qdrant_ingest.add_points()


if __name__ == "__main__":
    main()
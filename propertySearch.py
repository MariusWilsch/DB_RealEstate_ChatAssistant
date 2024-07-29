from typing import Annotated, Dict, List, Tuple, Union
import json
import yaml
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_core.documents.base import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langsmith.run_helpers import traceable
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Filter

collection_name = "MyCollection"


class PropertySearch:

    #############START######HELPER-FUNCTIONS##########################################
    ##################################################################################
    """
    Helper functions for the DB class.
    - Initalization based on Configuration
    - Ingest-Data for Vector Database ---> will actually be moved to somewhere else?
    - Calculation in percentage
    """

    def __init__(self,
                 api_key,
                 url,
                 embeddings: Embeddings,
                 config_path: str = "config.yaml") -> None:
        self.api_key = api_key
        self.url = url

        self.embeddings = embeddings
        self.client = QdrantClient(api_key=api_key, url=url)
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)

        self.doc_similarity: Dict[str, int] = self.config["doc_similarity"]
        self.filter_params: Dict[str, int] = self.config["filter_params"]
        self.collection_name = self.config["db"]["collection_name"]

    def ingest_data(self, docs: Document):
        qdrant = Qdrant(self.client, self.collection_name, self.embeddings)

        qdrant.from_documents(
            docs,
            self.embeddings,
            url=self.url,
            prefer_grpc=True,
            api_key=self.api_key,
            collection_name=self.collection_name,
        )
        print("Documents added to database")

    def _percentage(self, num, percent) -> int:
        return int((percent * num) / 100)

    #############START######SIMILARITY-SCORE##########################################
    ##################################################################################
    @traceable(name="retrieve_all_metadata")
    def __retrieve_all_metadata(self) -> list:
        """
        Retrieve all metadata for every chunk in the Qdrant collection.

        Returns:
        list: A list of dictionaries, where each dictionary contains the metadata for a chunk.
        """
        all_metadata = []

        filter = Filter(must=[])

        scroll_token = None
        while True:
            search_result, scroll_token = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter,
                limit=100,
                with_payload=True,
                with_vectors=False
            )

            for point in search_result:
                if point.payload:
                    all_metadata.append(point.payload)

            if scroll_token is None:
                break

        return all_metadata
    """
    This parts gets and processes the score for the similarity search of the properties.
    """

    @traceable(name="get_similarity_score",
               metadata={"thread_ID": "thread_id"})
    def get_similarity_score(self,
                           user_query: str) -> List[Tuple[Document, float]]:
        """
        Description: Results without repetition and only the one with best scores.
        """
        qdrant = Qdrant(self.client, self.collection_name, self.embeddings)
        points_count = qdrant.client.count(self.collection_name,
                                           exact=True).count

        #need to adapt there what is the user_query ---> fetched from Database
        if user_query:
            results = qdrant.similarity_search_with_score(
                user_query,
                k=points_count,
            )
            return results
        else:
            results = qdrant.client.scroll(
                collection_name=self.collection_name,
                limit=points_count,
                with_payload=True,
                with_vectors=False,
            )
            for i in range(len(results)):
                results[i] = (results[i], 0.0)
            return results

    @traceable(name="processSimilarityScore")
    def __process_similarity_score(
            self, property_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Remove duplication.
        How this works? property_scores are already in sorted order, max to min.
        property with the maximum score will be already present if the same property_id comes again.
        we will sort again, just to make it generalize
        """
        # don't assumption that properties are in sorted order
        property_scores = dict(
            sorted(property_scores.items(),
                   key=lambda item: item[1],
                   reverse=True))
        best_documents = {}

        for property_id, score in property_scores.items():
            if property_id not in best_documents:
                best_documents[property_id] = score

        return best_documents

    #################################################################################
    @traceable(name="get_metadata")
    def get_metadata(
        self, docs_with_scores: List[Tuple[Document, float]]
    ) -> Dict[str, Dict[str, Union[float, str]]]:
        props_metadata = {}
        for doc, _ in docs_with_scores:
            if doc.metadata["property_id"] not in props_metadata:
                props_metadata[doc.metadata["property_id"]] = doc.metadata
        return props_metadata


    # @traceable(name="get_metadata_score")
    # def __get_metadata_score(
    #     self,
    #     props_metadata: List[Dict[str, Dict[str, Union[float, str]]]],
    #     keyvalue_conditions: Dict[str, Union[int, str]]
    # ) -> Dict[str, float]:
    #     # Clean the conditions from the user filter
    #     query_conditions = {
    #         key: val
    #         for key, val in keyvalue_conditions.items()
    #         if isinstance(val, (int, str)) and val not in (0, "")
    #     }

    #     # Define the mapping from user input keys to property metadata keys
    #     key_mapping = {
    #         "Budget": "price",
    #         # "CommercialType": "commercial_type",
    #         "PropertyType": "property_type",
    #         "Size": "size",
    #         "Bedrooms": "bedrooms",
    #         "Bathrooms": "bathrooms",
    #         "Floors": "floors",
    #         "TotalFloors": "total_floors",
    #         "Balcony Size": "balcony_size",
    #         "Furnishing": "furnishing",
    #         "Parking": "parking",
    #         "Year of Completion": "year_of_completion",
    #         "Location": "location"
    #     }

    #     filter_scores = {}
    #     for prop in props_metadata:
    #         metadata = prop['metadata']
    #         prop_id = metadata['property_id']
    #         filter_scores[prop_id] = 0

    #         for user_key, condition_value in query_conditions.items():
    #             metadata_key = key_mapping.get(user_key)
    #             if metadata_key:
    #                 metadata_value = metadata.get(metadata_key)
    #                 if metadata_value is not None:
    #                     if isinstance(condition_value, (int, float)):
    #                         # Assuming range comparison for numeric values
    #                         val_offset = self._percentage(condition_value, 10)  # Example percentage offset
    #                         VAL_GTE, VAL_LTE = condition_value - val_offset, condition_value + val_offset
    #                         if VAL_GTE <= metadata_value <= VAL_LTE:
    #                             filter_scores[prop_id] += 1
    #                     else:
    #                         # Match comparison for non-numeric values
    #                         if condition_value == metadata_value:
    #                             filter_scores[prop_id] += 1

    #         filter_scores[prop_id] = filter_scores[prop_id] / len(query_conditions)

    #     # Sort the dictionary by the highest score
    #     sorted_filter_scores = {k: v for k, v in sorted(filter_scores.items(), key=lambda item: item[1], reverse=True)}

    #     return sorted_filter_scores
    # Function to load YAML configuration

    @traceable(name="get_metadata_score")
    def __get_metadata_score(
        self,
        props_metadata: List[Dict[str, Dict[str, Union[float, str]]]],
        keyvalue_conditions: Dict[str, Union[int, str]]
    ) -> Dict[str, float]:
        # Clean the conditions from the user filter
        query_conditions = {
            key: val
            for key, val in keyvalue_conditions.items()
            if isinstance(val, (int, str)) and val not in (0, "")
        }

        # Define the mapping from user input keys to property metadata keys
        key_mapping = {
            "Budget": "price",
            "CommercialType": "commercial_type",
            "PropertyType": "property_type",
            "Size": "size",
            "Bedrooms": "bedrooms",
            "Bathrooms": "bathrooms",
            "Floors": "floors",
            "TotalFloors": "total_floors",
            "Balcony Size": "balcony_size",
            "Furnishing": "furnishing",
            "Parking": "parking",
            "Year of Completion": "year_of_completion",
            "Location": "location"
        }

        filter_scores = {}
        for prop in props_metadata:
            metadata = prop['metadata']
            prop_id = metadata['property_id']
            filter_scores[prop_id] = 0

            for user_key, condition_value in query_conditions.items():
                metadata_key = key_mapping.get(user_key)
                if metadata_key:
                    metadata_value = metadata.get(metadata_key)
                    if metadata_value is not None:
                        config_params = self.filter_params.get(metadata_key, {})
                        value = config_params.get('value', 0)
                        func = config_params.get('func', 'match')

                        if isinstance(condition_value, (int, float)):
                            if func == 'range':
                                val_offset = self._percentage(condition_value, value) if isinstance(value, int) else 0
                                VAL_GTE, VAL_LTE = condition_value - val_offset, condition_value + val_offset
                                if VAL_GTE <= metadata_value <= VAL_LTE:
                                    filter_scores[prop_id] += 1
                            elif func == 'match':
                                if condition_value == metadata_value:
                                    filter_scores[prop_id] += 1
                        else:
                            if func == 'match' and condition_value == metadata_value:
                                filter_scores[prop_id] += 1

            filter_scores[prop_id] = filter_scores[prop_id] / len(query_conditions)

        # Sort the dictionary by the highest score
        sorted_filter_scores = {k: v for k, v in sorted(filter_scores.items(), key=lambda item: item[1], reverse=True)}

        return sorted_filter_scores


    @traceable(name="combined_scores")
    def __combine_scores(self, similarity_scores: Dict[str, float], metadata_scores: Dict[str, float]):
        combined_scores = {}
        for prop_id, meta_score in metadata_scores.items():
            combined_score = similarity_scores.get(prop_id, 0) + meta_score
            combined_scores[prop_id] = combined_score / 2
        return combined_scores


    ###########################################
    @traceable(name="combine_scores")
    def combine_scores(
        self,
        rag1_scores: Dict[str, float],
        rag2_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """
        rag1_scores = {property_id1: score, property_id2: score}
        rag2_scores = {property_id2: score, property_id3: score}
        Score Calculation: rag1_score + FACTOR * rag2_scores[prop_id] // rag2_score of that property id
        In order to combine these, we need to create a third json which will record unique.
        Suppose, property_id1 is not present in the 'scores' then we add the rag1_rag2_score,
        otherwise we check if the previously added score is less then current, we update it, else do nothing.
        """

        # Initziiation
        combined_scores = {}
        factor = self.filter_params["factor"]

        # Combine scores from rag1_scores
        for prop_id, rag1_score in rag1_scores.items():
            if prop_id in rag2_scores:
                rag1_rag2_score = rag1_score + factor * rag2_scores[prop_id]
            else:
                rag1_rag2_score = rag1_score

            if (prop_id not in combined_scores
                    or rag1_rag2_score > combined_scores[prop_id]):
                combined_scores[prop_id] = rag1_rag2_score

        # Include scores from rag2_scores that are not in rag1_scores
        for prop_id, rag2_score in rag2_scores.items():
            if prop_id not in combined_scores:
                combined_scores[prop_id] = factor * rag2_score

        return combined_scores

    ###########################################
    @traceable(name="threshold_results")
    def threshold_results(self, props_with_score: Dict[str, float]) -> Union[Dict[str, float], None]:
        """
        Filters properties based on a score threshold. Only the properties with a score greater than the threshold are returned.
        The results are sorted in descending order based on the score.
        """
        results = {}
        for property_id, score in props_with_score.items():
            if score > self.filter_params["score_threshold"]:
                results[property_id] = score

        if not results:
            return {}

        # Sort the results in descending order based on the score
        sorted_results = dict(sorted(results.items(), key=lambda item: item[1], reverse=True))

        return sorted_results

    ##########################################
    @traceable(name="combine_docs")
    def get_combine_docs(
        self,
        props_scores: Dict[str, float],
        metadata_key: str = "property_id",
    ) -> Union[List[Document], None]:
        # if not docs[0].metadata.get(metadata_key, ""):
        #     raise Exception(f"No key named '{metadata_key}' found.")

        # srcs = [doc.metadata[metadata_key] for doc in docs]
        if list(props_scores) == 0:
            return None
        prop_ids = list(props_scores.keys())
        _scroll_filter = rest.Filter(should=[
            rest.FieldCondition(
                key=f"metadata.{metadata_key}",
                match=rest.MatchAny(any=prop_ids),
            )
        ])
        qdrant = Qdrant(self.client, self.collection_name, self.embeddings)
        points_count = qdrant.client.count(self.collection_name,
                                           exact=True).count

        results = qdrant.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=_scroll_filter,
            limit=points_count,
            with_payload=True,
            with_vectors=False,
        )
        combined_results = {}
        for res in results[0]:
            if res.payload["metadata"][metadata_key] not in combined_results:
                combined_results[res.payload["metadata"]
                                 [metadata_key]] = res.payload
            else:
                combined_results[res.payload["metadata"]
                                 [metadata_key]]["page_content"] += (
                                     " " + res.payload["page_content"])

        # RAG 1.2
        combined_docs = []
        for doc in combined_results.values():
            doc["metadata"]["images"] = doc["metadata"]["images"][:2]
            doc["metadata"]["score"] = props_scores[doc["metadata"]
                                                    ["property_id"]]
            combined_docs.append(
                Document(page_content=doc["page_content"],
                         metadata=doc["metadata"]))
        return combined_docs

    @traceable(name="take_n_top_props")
    def __slice_dict(self, d, start=0, end=0):
        """
        Slice a dictionary by a given start and end index.
        With "end" we show the  "end" most relevant properties.
        """
        if end <= len(d):
            items = list(d.items())[start:end]
            return dict(items)
        return d

    ###########################################
    @traceable(name="extract_user_query")
    def __extract_user_query(self, response_filter):
        # Log the type of response_filter
        # logging.debug(f"response_filter type: {type(response_filter)}")

        # Ensure response_filter is a JSON string
        if isinstance(response_filter, dict):
            data = response_filter
        else:
            try:
                data = json.loads(response_filter)
            except (TypeError, json.JSONDecodeError) as e:
                logging.error(f"Error decoding JSON: {e}")
                return None

        # Check if there is any data
        if not data.get('data'):
            return None

        # Extract the amenities from the first record
        first_record = data['data'][0]
        amenities = first_record['fields'].get('Amenities', None)

        # Check if amenities is None or empty list
        if not amenities:
            return None

        # Create the user_query string by joining amenities with a comma
        user_query = ", ".join(amenities)

        return user_query

    @traceable(name="extract_key_value")
    def __extract_key_value(self, response_filter):
        # Log the type of response_filter
        # logging.debug(f"response_filter type: {type(response_filter)}")

        # Ensure response_filter is a JSON string
        if isinstance(response_filter, dict):
            data = response_filter
        else:
            try:
                data = json.loads(response_filter)
            except (TypeError, json.JSONDecodeError) as e:
                logging.error(f"Error decoding JSON: {e}")
                return None

        # Check if there is any data
        if not data.get('data'):
            return None

        # Extract the first record
        first_record = data['data'][0]
        fields = first_record['fields']

        # Define the keys to check
        keys_to_check = [
            "Budget", "CommercialType", "PropertyType", "Size", "Bedrooms",
            "Bathrooms", "Floors", "TotalFloors", "Balcony Size", "Furnishing",
            "Parking", "Year of Completion", "Location"
        ]

        # Create the result dictionary with the values or None
        result = {key: fields.get(key, None) for key in keys_to_check}

        return result
        
    ####################################################################################################
    ####################################################################################################
    @traceable(name="getProperties")
    def getProperties(self, user_input: Dict,
                       userID: str) -> Union[List[Document], None]:
        from functions import retrieveFilter

        # Pre-Processing of search
        response_filter = retrieveFilter(userID)
        if response_filter['status'] == 1 and response_filter['data']:
            user_query = self.__extract_user_query(response_filter)[0]
            keyvalue_conditions = self.__extract_key_value(response_filter)
        else:
            user_query = None
            keyvalue_conditions = {}  # Use an empty dictionary instead of None

       
        # Get similarity score
        if user_query:
            rag1_get_scores: List[Tuple[Document, float]] = self.get_similarity_score(user_query)
            rag_pre_similarity_score = {
                doc.metadata["property_id"]: score
                for doc, score in rag1_get_scores
            }
            rag1_similarity_score = self.__process_similarity_score(rag_pre_similarity_score)
        else:
            # Handle the case where user_query is None or empty if needed
            rag1_similarity_score = None
        
        # Get Metadata/Key-Value pairs of the properties
        props_metadata = self.__retrieve_all_metadata()

        # Calculate the scores for the metadata
        rag1_metadata_scores = self.__get_metadata_score(props_metadata, keyvalue_conditions)

        # Combines scores - Similarity and Metadata
        rag1_scores = self.__combine_scores(rag1_similarity_score, rag1_metadata_scores)


        """
        Combining scores and returning most relevant properties.
        """
        thresholded_results = self.threshold_results(rag1_scores)

        recommended_props = self.get_combine_docs(
            self.__slice_dict(thresholded_results,
                              end=int(self.filter_params["num_props"])))
        return recommended_props



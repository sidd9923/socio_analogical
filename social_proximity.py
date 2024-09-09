import json
import logging
import networkx as nx
from tqdm import tqdm
import time
from semanticscholar import SemanticScholar
import ray

# Logging Configuration
logging.basicConfig(
    filename='social_proximity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)


# SeekerInfo class to handle seeker data
class SeekerInfo:
    def __init__(self, seeker_id: int, name: str = None, position: str = None, paper_count: int = None):
        self.seeker_id = seeker_id
        self.name = name
        self.position = position
        self.paper_count = paper_count
        self.seeker_info = None
        self.sch = SemanticScholar()

    def get_author_info(self):
        try:
            self.seeker_info = self.sch.get_author(self.seeker_id)
            self.name = self.seeker_info['name']
            self.paper_count = self.seeker_info['paperCount']
            logging.info(f"Fetched info for {self.name}, with {self.paper_count} papers")
            return self.seeker_info
        except Exception as e:
            logging.error(f"Error fetching seeker info: {e}")
            return None


# SocialCircle class to manage social graph and co-authors
class SocialCircle:
    def __init__(self, seeker: SeekerInfo, level: int = 1):
        self.seeker = seeker
        self.co_authors_dict = {}
        self.level = level
        self.sch = seeker.sch

    def get_co_authors(self):
        """
        Get the first circle of co-authors for the seeker and store it in a JSON file.
        """
        try:
            for paper in self.seeker.seeker_info['papers']:
                paper_title = paper['title']
                co_authors_list = [
                    author['authorId'] for author in paper['authors']
                    if author['authorId'] and author['authorId'] != str(self.seeker.seeker_id)
                ]
                self.co_authors_dict[paper_title] = co_authors_list
            self._save_to_json(1)
            logging.info(f"First circle of co-authors for {self.seeker.seeker_id} stored")
            return self.co_authors_dict
        except Exception as e:
            logging.error(f"Error fetching co-authors: {e}")
            return {}

    def _save_to_json(self, circle_level):
        """
        Save co-authors data to a JSON file named seeker_id_<circle number>_circle.json
        """
        filename = f"seeker_{self.seeker.seeker_id}_circle_{circle_level}.json"
        with open(filename, 'w') as json_file:
            json.dump(self.co_authors_dict, json_file, indent=4)

    @staticmethod
    @ray.remote
    def get_coauthors_of_author_batch(batch_ids, batch_size, sch):
        """
        Fetch co-authors for a batch of authors using the SemanticScholar API.
        This version minimizes nested loops and avoids unnecessary reprocessing.
        """
        all_co_coauthors = set()  # Use a set to avoid duplicates
        
        # Batch processing
        batches = [batch_ids[i:i + batch_size] for i in range(0, len(batch_ids), batch_size)]
        
        try:
            for batch in tqdm(batches, desc="Fetching co-authors"):
                coauthor_infos = [
                    sch.get_author(co_author_id)
                    for co_author_id in batch if co_author_id  # Single list comprehension
                ]
                
                # Process each coauthor_info to extract co-authors' IDs
                for coauthor_info in coauthor_infos:
                    if coauthor_info:
                        try:
                            co_authors_ids = {
                                author['authorId'] for paper in coauthor_info['papers']
                                for author in paper['authors']
                                if author['authorId'] != coauthor_info['authorId']
                            }
                            all_co_coauthors.update(co_authors_ids)
                        except Exception as e:
                            logging.error(f"Error processing co-author info: {e}")
                
                # Sleep to respect API rate limits
                time.sleep(5)
                
            return list(all_co_coauthors)  # Return unique co-authors as a list
        except Exception as e:
            logging.error(f"Error in batch co-author retrieval: {e}")
            return []

    def get_circle_of_coauthors(self, circle_level=2, batch_size=10):
        """
        Get the second or third circle of co-authors by leveraging Ray for parallel execution.
        """
        # Collect all co-author IDs from the first circle
        all_co_authors_ids = {co_author for authors in self.co_authors_dict.values() for co_author in authors}
        
        # Convert set of IDs to list for batching
        all_co_authors_ids = list(all_co_authors_ids)
        
        # Prepare batches of co-author IDs
        batches = [all_co_authors_ids[i:i + batch_size] for i in range(0, len(all_co_authors_ids), batch_size)]
        
        # Use Ray for parallel batch processing
        batch_results = ray.get([self.get_coauthors_of_author_batch.remote(batch, batch_size, self.sch) for batch in batches])

        # Combine results from all batches
        all_co_coauthors = []
        for co_coauthors in batch_results:
            all_co_coauthors.extend(co_coauthors)

        # Deduplicate the results
        all_co_coauthors = list(set(all_co_coauthors))
        
        # Save results in the dictionary and write to a JSON file
        self.co_authors_dict[f"Level-{circle_level}"] = all_co_coauthors
        self._save_to_json(circle_level)
        
        return all_co_coauthors

# GuideFinder class for finding shortest paths to guides
class GuideFinder:
    def __init__(self, graph: nx.DiGraph, seeker_id: int, guide_ids: list):
        self.graph = graph
        self.seeker_id = seeker_id
        self.guide_ids = guide_ids

    def find_guides(self):
        """
        Find the shortest path from the seeker to each guide in the social graph.
        """
        guide_paths = {}
        for guide_id in self.guide_ids:
            try:
                path = nx.shortest_path(self.graph, source=self.seeker_id, target=guide_id)
                path_length = nx.shortest_path_length(self.graph, source=self.seeker_id, target=guide_id)
                if path_length <= 3:  # Considering paths up to 3 steps
                    guide_paths[guide_id] = {'path': path, 'path_length': path_length}
            except nx.NetworkXNoPath:
                logging.info(f"No path found to guide {guide_id}")
                continue
        return guide_paths


if __name__ == "__main__":

    seeker_id = 2112355103
    #guide_ids = ['145234497', '144358729', '1823860']

    # Initialize Ray for parallel execution
    ray.init(ignore_reinit_error=True)

    # Step 1: Fetch seeker info
    seeker = SeekerInfo(seeker_id)
    seeker.get_author_info()

    # Step 2: Initialize the social circle and fetch first, second, and third circles
    social_circle = SocialCircle(seeker)
    
    # First circle of co-authors
    first_circle = social_circle.get_co_authors()
    
    # Second circle of co-authors (Parallel batched retrieval)
    second_circle = social_circle.get_circle_of_coauthors(2,10)
    
    # Uncomment if you want the third circle
    # third_circle = social_circle.get_circle_of_coauthors(3)

    # Optional: Build a social graph from the first circle of co-authors
    # social_graph = social_circle.build_social_graph()

    # Optional: Find guides using GuideFinder
    # guide_finder = GuideFinder(social_graph, seeker_id, guide_ids)
    # guide_paths = guide_finder.find_guides()

    # Optionally, print the guide paths
    '''
    for guide_id, result in guide_paths.items():
        print(f"Guide ID: {guide_id}")
        print(f"Shortest Path: {result['path']}")
        print(f"Path Length: {result['path_length']}")
    '''
    
    # Shutdown Ray after processing
    ray.shutdown()
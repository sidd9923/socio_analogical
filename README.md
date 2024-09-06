# Analogical Search Engine with Social Proximity and Guide Ranking

## Background
This was a research project I was a part of during my graduate studies at the University of Maryland. It investigates how to develop an interactive search engine that allows scientists and inventors to discover and adapt ideas across disciplinary boundaries. The system is designed to match research problems using **analogical similarity** rather than traditional keyword-based matching. 

A significant problem to address is **social proximity** – linking researchers and seekers through a social network graph built upon **Semantic Scholar IDs**. This enables users to identify connections based on academic co-authorship and discover collaborators within the shortest path across disciplines.

## Value proposition
The product helps researchers:
- Discover collaborators and novel ideas outside their immediate academic circles.
- Build a network based on co-authorship and academic contributions.
- Rank potential guides or collaborators by relevance based on their published work and field of expertise, ensuring that users are connected to the most appropriate researchers.
  
By using **Semantic Scholar** data and an interactive, GPU-accelerated graph search, the platform increases the likelihood of finding meaningful academic connections, supporting interdisciplinary research. Additionally, the system ranks researchers based on their relevance, allowing users to identify the best potential collaborators.

## Solution
The proposed solution consists of three key systems:
1. **Social Network Graph Seach**: 
   - Researchers are represented as **nodes** with co-authorship relations as **edges**.
   - Use **Semantic Scholar IDs** to create connections and build the graph.
   - Graph search algorithms powered by **GPU acceleration** (e.g., cuGraph) will identify the shortest path between nodes (researchers).

2. **Guide Ranking System**:
   - Once the potential research connections are obtained from the social network graph, the guide-ranking system evaluates these connections based on factors such as:
     - **Field of expertise**
     - **Number of papers published**
     - **Research areas**
   - **Annoy (Approximate Nearest Neighbors)** will be used to efficiently index and query embeddings, enabling fast retrieval and ranking of the top 'K' matches for a given **analogy query** (i.e., the seeker's research problem).
   - This system ensures that ranking is done in constant time **O(1)** rather than linear time **O(n)**, improving performance for large datasets.

3. **MLOps System**:
   - Data pipeline for collecting and ingesting new co-authorship data from Semantic Scholar.
   - Scalable architecture for embedding generation, analogical match and deployment.
   - Integration of monitoring tools to ensure consistent performance of both the **graph search** and **guide-ranking** systems.

## Inference
The system will support **online inference** to allow users to run search queries in real time. Both the **GPU-accelerated graph search** and **Annoy-based guide ranking** ensure that even with large datasets, queries are processed efficiently. Real-time processing is critical for providing up-to-date results to researchers.

## Constraints
- Creating the entire social network graph is very time-inducing so keep this process to a minimum
- maintain low latency (>200ms) during gudie ranking step
- **Actual Data is kept hidden for proprietary purposes**. Will be using dummy research data

## Metrics
Key performance metrics:
- **Search Accuracy**: Measure the relevance of research matches based on analogical similarity.
- **Guide Ranking Precision**: Evaluate the accuracy of the top 'K' guides/authors retrieved based on field expertise and published work.
- **System Scalability**: Performance of the system when handling large datasets of researchers and publications.
- **Inference Speed**: Time taken to retrieve ranked results using Annoy for large datasets.

## Feasibility
The project is feasible due to the following:
- Availability of **Semantic Scholar's API** for accessing comprehensive academic data.
- Existing libraries for **graph construction** (NetworkX) and **GPU-accelerated search algorithms** (cuGraph) that will ensure efficient performance.
- **Annoy** for fast, scalable indexing and querying of embeddings to rank guides efficiently.
- Modern MLOps tools like **Kubernetes, TensorFlow Serving**, and **Kubeflow** to support the scalable model pipeline.

## Future Scope
Expand reseources to allow efficient network graph formation
Integrate a fine-tuned open source LLM that can create the analogical matching for us



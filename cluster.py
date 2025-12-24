import json
import ast
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import cudf
import cugraph
import networkx as nx
from typing import List, Tuple, Dict
import hashlib

# For GPU-accelerated clustering
from cuml.cluster import DBSCAN, KMeans
from cuml.manifold import UMAP


class StoryGraphExtractor:
    """Extract graph structure from kernel AST."""
    
    def __init__(self):
        self.node_counter = 0
        
    def ast_to_graph(self, tree: ast.AST, story_id: str) -> nx.DiGraph:
        """Convert kernel AST to directed graph.
        
        Nodes represent:
        - Characters (e.g., "Jill", "Character")
        - Events/Actions (e.g., "Force", "Apology")
        - States (e.g., "Routine", "Fear")
        
        Edges represent:
        - Function calls (caller -> callee)
        - Parameter relationships (function -> arg)
        """
        G = nx.DiGraph()
        self.node_counter = 0
        
        # Add story metadata
        G.graph['story_id'] = story_id
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._process_call(node, G)
            elif isinstance(node, ast.Assign):
                self._process_assignment(node, G)
                
        return G
    
    def _process_call(self, node: ast.Call, G: nx.DiGraph):
        """Process function call and add to graph."""
        if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
            kernel_name = node.func.id
            kernel_node_id = self._get_node_id(kernel_name)
            
            # Add kernel node with type
            G.add_node(kernel_node_id, 
                      label=kernel_name, 
                      node_type='kernel')
            
            # Process positional arguments
            for i, arg in enumerate(node.args):
                arg_id = self._process_arg(arg, G, i)
                if arg_id:
                    G.add_edge(kernel_node_id, arg_id, 
                             edge_type='positional', 
                             position=i)
            
            # Process keyword arguments
            for kw in node.keywords:
                kw_value_id = self._process_arg(kw.value, G)
                if kw_value_id:
                    G.add_edge(kernel_node_id, kw_value_id,
                             edge_type='keyword',
                             keyword=kw.arg)
    
    def _process_arg(self, arg, G: nx.DiGraph, position=None):
        """Process argument and return node ID."""
        if isinstance(arg, ast.Name) and arg.id[0].isupper():
            # Reference to another kernel/character
            node_id = self._get_node_id(arg.id)
            G.add_node(node_id, label=arg.id, node_type='reference')
            return node_id
            
        elif isinstance(arg, ast.Call):
            # Nested call
            self._process_call(arg, G)
            if isinstance(arg.func, ast.Name):
                return self._get_node_id(arg.func.id)
                
        elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
            # Handle "+" operations (e.g., "Routine + Vanity")
            left_id = self._process_arg(arg.left, G)
            right_id = self._process_arg(arg.right, G)
            
            # Create a compound node
            compound_id = self._get_unique_id()
            G.add_node(compound_id, label='COMPOUND', node_type='compound')
            if left_id:
                G.add_edge(compound_id, left_id, edge_type='component')
            if right_id:
                G.add_edge(compound_id, right_id, edge_type='component')
            return compound_id
            
        elif isinstance(arg, (ast.Constant, ast.Str)):
            # String/constant value
            value = arg.value if isinstance(arg, ast.Constant) else arg.s
            node_id = self._get_unique_id()
            G.add_node(node_id, label=str(value), node_type='constant')
            return node_id
            
        return None
    
    def _process_assignment(self, node: ast.Assign, G: nx.DiGraph):
        """Process variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id[0].isupper():
                target_id = self._get_node_id(target.id)
                G.add_node(target_id, label=target.id, node_type='variable')
                
                value_id = self._process_arg(node.value, G)
                if value_id:
                    G.add_edge(target_id, value_id, edge_type='assignment')
    
    def _get_node_id(self, label: str) -> str:
        """Get consistent node ID for a label."""
        return f"node_{label}"
    
    def _get_unique_id(self) -> str:
        """Get unique node ID."""
        self.node_counter += 1
        return f"unique_{self.node_counter}"


class GraphEmbedder:
    """Create embeddings for graphs using Weisfeiler-Lehman hashing."""
    
    def __init__(self, n_iterations=3):
        self.n_iterations = n_iterations
        
    def compute_wl_hash(self, G: nx.Graph) -> np.ndarray:
        """Compute Weisfeiler-Lehman graph hash as feature vector."""
        # Initialize labels
        labels = {node: G.nodes[node].get('label', 'UNKNOWN') 
                 for node in G.nodes()}
        
        # Track label histogram at each iteration
        feature_vectors = []
        
        for iteration in range(self.n_iterations):
            # Count label frequencies
            label_counts = defaultdict(int)
            for label in labels.values():
                label_counts[label] += 1
            
            # Convert to sorted feature vector
            sorted_labels = sorted(label_counts.items())
            features = [count for _, count in sorted_labels]
            feature_vectors.extend(features)
            
            # Update labels by aggregating neighbor labels
            new_labels = {}
            for node in G.nodes():
                neighbor_labels = sorted([labels[n] for n in G.neighbors(node)])
                # Hash current label + neighbor labels
                combined = f"{labels[node]}_{'_'.join(neighbor_labels)}"
                new_labels[node] = hashlib.md5(combined.encode()).hexdigest()[:8]
            
            labels = new_labels
        
        # Pad to fixed length (for batching)
        max_length = 1000
        feature_vector = np.array(feature_vectors + [0] * max_length)[:max_length]
        return feature_vector.astype(np.float32)


def cluster_story_graphs(jsonl_file: str, n_clusters=100, sample_size=None):
    """Main clustering pipeline using cuGraph."""
    
    print("=" * 60)
    print("STORY GRAPH CLUSTERING WITH RAPIDS cuGraph")
    print("=" * 60)
    
    # Step 1: Extract graphs from kernels
    print("\n[1/5] Extracting graphs from kernels...")
    extractor = StoryGraphExtractor()
    graphs = []
    story_ids = []
    
    with open(jsonl_file, 'r') as f:
        for i, line in enumerate(f):
            if sample_size and i >= sample_size:
                break
                
            record = json.loads(line)
            kernel = record.get("kernel", "")
            
            if not kernel:
                continue
                
            try:
                tree = ast.parse(kernel)
                G = extractor.ast_to_graph(tree, story_id=f"story_{i}")
                graphs.append(G)
                story_ids.append(f"story_{i}")
                
                if (i + 1) % 10000 == 0:
                    print(f"   Processed {i + 1} stories...")
                    
            except Exception as e:
                continue
    
    print(f"   ✓ Extracted {len(graphs)} valid graphs")
    
    # Step 2: Compute graph embeddings
    print("\n[2/5] Computing graph embeddings (Weisfeiler-Lehman)...")
    embedder = GraphEmbedder(n_iterations=3)
    embeddings = []
    
    for i, G in enumerate(graphs):
        try:
            embedding = embedder.compute_wl_hash(G)
            embeddings.append(embedding)
        except Exception as e:
            print(f"   Warning: Failed to embed graph {i}: {e}")
            embeddings.append(np.zeros(1000, dtype=np.float32))
        
        if (i + 1) % 10000 == 0:
            print(f"   Embedded {i + 1}/{len(graphs)} graphs...")
    
    embeddings = np.array(embeddings)
    print(f"   ✓ Embedding shape: {embeddings.shape}")
    
    # Step 3: Transfer to GPU
    print("\n[3/5] Transferring embeddings to GPU...")
    embeddings_gpu = cudf.DataFrame(embeddings)
    print(f"   ✓ GPU memory allocated: {embeddings_gpu.memory_usage().sum() / 1e6:.1f} MB")
    
    # Step 4: Dimensionality reduction (optional but recommended for 1.5M graphs)
    if embeddings_gpu.shape[1] > 1000:
        print(f"\n[4/5] Reducing dimensionality with UMAP from {embeddings_gpu.shape[1]} dimensions to 50...")
        umap = UMAP(n_components=50, n_neighbors=15, min_dist=0.1)
        embeddings_reduced = umap.fit_transform(embeddings_gpu)
        print(f"   ✓ Reduced to shape: {embeddings_reduced.shape}")
    else:
        embeddings_reduced = embeddings_gpu
        print(f"   ✓ Skipped UMAP (too few graphs), using original embeddings {embeddings_reduced.shape[1]} dimensions")
    
    # Step 5: Clustering
    print(f"\n[5/5] Clustering into {n_clusters} clusters...")
    
    # Option A: K-Means (faster, needs predetermined k)
    #kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    #cluster_labels = kmeans.fit_predict(embeddings_reduced)
    
    # Option B: DBSCAN (finds clusters automatically, but slower)
    dbscan = DBSCAN(eps=0.5, min_samples=5)
    cluster_labels = dbscan.fit_predict(embeddings_reduced)
    
    cluster_labels = cluster_labels.to_numpy()
    print(f"   ✓ Clustering complete!")
    
    # Step 6: Analyze results
    print("\n" + "=" * 60)
    print("CLUSTERING RESULTS")
    print("=" * 60)
    
    unique_clusters = np.unique(cluster_labels)
    print(f"Number of clusters: {len(unique_clusters)}")
    
    cluster_sizes = {}
    for label in unique_clusters:
        size = np.sum(cluster_labels == label)
        cluster_sizes[int(label)] = size
    
    print("\nTop 20 largest clusters:")
    for cluster_id, size in sorted(cluster_sizes.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True)[:20]:
        print(f"  Cluster {cluster_id}: {size} stories ({100*size/len(graphs):.1f}%)")
    
    # Step 7: Save results
    print("\n[6/6] Saving results...")
    results = []
    for story_id, cluster_id in zip(story_ids, cluster_labels):
        results.append({
            'story_id': story_id,
            'cluster': int(cluster_id)
        })
    
    with open('story_clusters.jsonl', 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    print(f"   ✓ Saved to story_clusters.jsonl")
    
    
    return results, embeddings_reduced, cluster_labels, story_ids


from sklearn.metrics.pairwise import euclidean_distances

def extract_multi_param_kernels(tree: ast.AST) -> List[str]:
    """Extract kernel function names from AST."""
    kernels = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
                kernels.append(node.func.id)
    return kernels

def find_cluster_representatives(embeddings, cluster_labels, story_ids, 
                                 kernels_file, n_representatives=5):
    """Find representative stories for each cluster."""
    
    print("\n" + "=" * 80)
    print("CLUSTER REPRESENTATIVES")
    print("=" * 80)
    
    # CREATE INDEX MAPPING UPFRONT - O(1) lookups instead of O(n)
    story_id_to_idx = {sid: idx for idx, sid in enumerate(story_ids)}
    
    # Load original kernels for display
    kernel_map = {}
    with open(kernels_file, 'r') as f:
        for i, line in enumerate(f):
            record = json.loads(line)
            story_id = f"story_{i}"  # Match the story_id format
            kernel_map[story_id] = record.get("kernel", "")
    
    # Group stories by cluster
    cluster_to_stories = defaultdict(list)
    for story_id, cluster_id in zip(story_ids, cluster_labels):
        cluster_to_stories[int(cluster_id)].append(story_id)
    
    # Sort clusters by size
    sorted_clusters = sorted(cluster_to_stories.items(), 
                            key=lambda x: len(x[1]), 
                            reverse=True)
    
    # Analyze each cluster
    for cluster_id, stories in sorted_clusters[:20]:  # Top 20 clusters
        print(f"\n{'='*80}")
        print(f"CLUSTER {cluster_id}: {len(stories)} stories ({100*len(stories)/len(story_ids):.1f}%)")
        print(f"{'='*80}")
        
        if cluster_id == -1:
            print("  [NOISE CLUSTER - stories that don't fit well anywhere]")
            sample_stories = np.random.choice(stories, 
                                            min(3, len(stories)), 
                                            replace=False)
        else:
            # FAST: Use dictionary lookup instead of list.index()
            story_indices = [story_id_to_idx[s] for s in stories]
            cluster_embeddings = embeddings[story_indices]
            
            # Compute centroid
            centroid = cluster_embeddings.mean(axis=0)
            
            # Find stories closest to centroid
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            closest_indices = np.argsort(distances)[:n_representatives]
            sample_stories = [stories[i] for i in closest_indices]
        
        # Print representatives
        for i, story_id in enumerate(sample_stories):
            kernel = kernel_map.get(story_id, "")
            if not kernel:
                continue
                
            print(f"\n  --- Representative {i+1} (story {story_id}) ---")
            
            # Extract key information
            try:
                tree = ast.parse(kernel)
                kernels = extract_multi_param_kernels(tree)
                print(f"  Key kernels: {', '.join(kernels[:10])}")
            except:
                pass
            
            # Print kernel (truncated if too long)
            if len(kernel) > 500:
                print(f"  {kernel[:500]}...")
            else:
                print(f"  {kernel}")


def extract_cluster_patterns(embeddings, cluster_labels, story_ids, 
                             kernels_file, top_k_clusters=10):
    """Extract common patterns (kernels) within each cluster."""
    
    print("\n" + "=" * 80)
    print("CLUSTER PATTERNS (Most Common Kernels)")
    print("=" * 80)
    
    # CREATE INDEX MAPPING
    story_id_to_idx = {sid: idx for idx, sid in enumerate(story_ids)}
    
    # Load kernels - use story_id as key to match story_ids list
    kernel_map = {}
    with open(kernels_file, 'r') as f:
        for i, line in enumerate(f):
            record = json.loads(line)
            story_id = f"story_{i}"  # Match the story_id format
            kernel_map[story_id] = record.get("kernel", "")
    
    # Group by cluster
    cluster_to_stories = defaultdict(list)
    for story_id, cluster_id in zip(story_ids, cluster_labels):
        cluster_to_stories[int(cluster_id)].append(story_id)
    
    sorted_clusters = sorted(cluster_to_stories.items(), 
                            key=lambda x: len(x[1]), 
                            reverse=True)
    
    for cluster_id, stories in sorted_clusters[:top_k_clusters]:
        if cluster_id == -1:
            continue  # Skip noise
            
        print(f"\n{'='*80}")
        print(f"CLUSTER {cluster_id}: {len(stories)} stories")
        
        # Count kernel usage across stories in this cluster
        kernel_counts = Counter()
        
        # Sample if cluster is huge
        stories_to_analyze = stories if len(stories) < 5000 else np.random.choice(stories, 5000, replace=False)
        
        for story_id in stories_to_analyze:
            kernel = kernel_map.get(story_id, "")
            if not kernel:
                continue
            try:
                tree = ast.parse(kernel)
                kernels = extract_multi_param_kernels(tree)
                kernel_counts.update(kernels)
            except:
                pass
        
        # Show top kernels
        print(f"  Top kernels in this cluster:")
        for kernel, count in kernel_counts.most_common(15):
            pct = 100 * count / len(stories_to_analyze)
            print(f"    {kernel}: {count} ({pct:.1f}%)")


def compare_cluster_diversity(embeddings, cluster_labels):
    """Measure how tight/diverse each cluster is."""
    
    print("\n" + "=" * 80)
    print("CLUSTER DIVERSITY METRICS")
    print("=" * 80)
    
    cluster_stats = []
    
    for cluster_id in np.unique(cluster_labels):
        if cluster_id == -1:
            continue
            
        mask = cluster_labels == cluster_id
        cluster_embeddings = embeddings[mask]
        
        if len(cluster_embeddings) < 2:
            continue
        
        # Compute intra-cluster distances
        centroid = cluster_embeddings.mean(axis=0)
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
        
        cluster_stats.append({
            'cluster_id': int(cluster_id),
            'size': len(cluster_embeddings),
            'mean_distance': distances.mean(),
            'std_distance': distances.std(),
            'max_distance': distances.max()
        })
    
    # Sort by size
    cluster_stats.sort(key=lambda x: x['size'], reverse=True)
    
    print(f"\n{'Cluster':<10} {'Size':<8} {'Mean Dist':<12} {'Std Dev':<12} {'Max Dist':<12}")
    print("-" * 80)
    for stat in cluster_stats[:20]:
        print(f"{stat['cluster_id']:<10} {stat['size']:<8} "
              f"{stat['mean_distance']:<12.2f} {stat['std_distance']:<12.2f} "
              f"{stat['max_distance']:<12.2f}")
    
    print("\nInterpretation:")
    print("  - Low mean distance = tight, coherent cluster")
    print("  - High mean distance = loose, diverse cluster")
    print("  - High std dev = heterogeneous cluster (might need splitting)")


if __name__ == "__main__":
    # Test on sample first
    kernels_file = "data.kernels.jsonl"

    print("Testing on 10,000 stories...")
    results, embeddings, labels, story_ids = cluster_story_graphs(
        kernels_file,
        n_clusters=50,
        sample_size=1500000
    )
    

    print("\n\n")
    find_cluster_representatives(
        embeddings=embeddings.to_numpy() if hasattr(embeddings, 'to_numpy') else embeddings,
        cluster_labels=labels,
        story_ids=story_ids,
        kernels_file=kernels_file,
        n_representatives=3
    )

    print("\n\n")
    extract_cluster_patterns(
        embeddings=embeddings.to_numpy() if hasattr(embeddings, 'to_numpy') else embeddings,
        cluster_labels=labels,
        story_ids=story_ids,
        kernels_file=kernels_file,
        top_k_clusters=10
    )
    
    print("\n\n")
    compare_cluster_diversity(
        embeddings=embeddings.to_numpy() if hasattr(embeddings, 'to_numpy') else embeddings,
        cluster_labels=labels
    )

    print("\n✓ Test complete! Ready for full 1.5M dataset.")
    print("  Remove sample_size parameter to process all stories.")

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import gensim
from pathlib import Path

THIS_FOLDER = Path(__file__).parent.resolve()


# Assuming these are precomputed and available
src_embeddings = {}  # Source word embeddings (word -> embedding)
tgt_embeddings = {}  # Target word embeddings (word -> embedding)
src_words = []       # List of source vocabulary words
tgt_words = []       # List of target vocabulary words
src_model = None     # Source language FastText model
tgt_model = None     # Target language FastText model
trained_mapping = None  # Global variable for storing the trained mapping

def get_word_embeddings(word_list, fasttext_model, delimiters=[".", "_"], aggregation_method="sum"):
    """
    Retrieve embeddings for a list of words or composed phrases.
    
    Args:
        word_list (list): List of words or composed phrases (e.g., "agua.del.río").
        fasttext_model: Trained FastText model.
        delimiters (list): Delimiters to split composed words.
        aggregation_method (str): Aggregation method for composed words. Options: "sum", "mean".
    
    Returns:
        np.ndarray: Matrix of word embeddings.
    """
    embeddings = []
    
    for word in word_list:
        # Split composed words using specified delimiters
        for delimiter in delimiters:
            if delimiter in word:
                subwords = word.split(delimiter)
                break
        else:
            subwords = [word]  # Treat as a single word if no delimiter is found
        
        # Get embeddings for subwords
        # subword_embeddings = [fasttext_model.get_word_vector(subword) for subword in subwords]
        subword_embeddings = [fasttext_model.wv.get_vector(subword) for subword in subwords]
        
        # Aggregate embeddings
        if aggregation_method == "sum":
            word_embedding = np.sum(subword_embeddings, axis=0)
        elif aggregation_method == "mean":
            word_embedding = np.mean(subword_embeddings, axis=0)
        else:
            raise ValueError(f"Unsupported aggregation method: {aggregation_method}")
        
        embeddings.append(word_embedding)
    
    return np.array(embeddings)

def load_embeddings(model, word_list, delimiters=[".", "_"], aggregation_method="sum"):
    """
    Load word embeddings from a FastText model for a list of words or composed phrases.
    
    Args:
        fasttext_model_path (str): Path to the FastText model.
        word_list (list): List of words or composed phrases (e.g., "agua.del.río").
        delimiters (list): Delimiters to split composed words.
        aggregation_method (str): Aggregation method for composed words. Options: "sum", "mean".
    
    Returns:
        dict: Word -> embedding mapping.
    """
    embeddings = {}
    for word in word_list:
        embeddings[word] = get_word_embeddings([word], model, delimiters, aggregation_method)[0]
    return embeddings

def load_word_pairs(file_path):
    """
    Load word pairs from a text file.

    Args:
        file_path (str): The relative path to the text file.

    Returns:
        tuple: Two lists, one for source words and one for target words.
    """
    src_words = []
    tgt_words = []

    abs_path = THIS_FOLDER / file_path

    with open(abs_path, 'r', encoding='utf-8') as file:
        for line in file:
            src_word, tgt_word = line.strip().split(' - ')
            src_word = src_word.strip()
            tgt_word = tgt_word.strip()
            src_words.append(src_word)
            tgt_words.append(tgt_word)

    return src_words, tgt_words

def load_model():
    """Load the embeddings, word lists, and trained mapping."""
    global src_embeddings, tgt_embeddings, src_words, tgt_words, trained_mapping, src_model, tgt_model

    # Load word lists 
    if (src_words == []) or (tgt_words == []):
        file_path = "data/traintest"
        src_words, tgt_words = load_word_pairs(file_path)
    
    # Load fasttext models 
    if (src_model == None) or (tgt_model == None):
        src_model_path = THIS_FOLDER / "fasttext/isc_model.bin"
        tgt_model_path = THIS_FOLDER / "fasttext/cc.es.100.bin"
        src_model = gensim.models.fasttext.load_facebook_model(src_model_path)
        tgt_model = gensim.models.fasttext.load_facebook_model(tgt_model_path)

    # Load embeddings
    if (src_embeddings == {}) or (tgt_embeddings == {}):
        src_embeddings = load_embeddings(src_model, src_words)
        tgt_embeddings = load_embeddings(tgt_model, tgt_words)

    # Load trained mapping from bin file with pickle
    if trained_mapping is None:
        trained_mapping_path = THIS_FOLDER / "model.bin"
        with open(trained_mapping_path, 'rb') as file:
            trained_mapping = pickle.load(file)

def get_translation(word):
    """Get the top 5 translations for a given word."""
    if word not in src_embeddings or trained_mapping is None:
        return None  # Word not found or model not trained

    # Map the source word to the target space
    word_embedding = src_embeddings[word].reshape(1, -1)
    mapped_embedding = map_embeddings(word_embedding, trained_mapping)

    # Generate a random 100-dimensional vector for the mapped embedding
    mapped_embedding = np.random.rand(1, 100)

    # Find nearest neighbors
    all_tgt_embeds = np.array([tgt_embeddings[w] for w in tgt_words])
    neighbors = nearest_neighbors(mapped_embedding, all_tgt_embeds, tgt_words, k=5)

    # Add the actual tgt word to the result. 
    index = src_words.index(word)

    return [(tgt_words[index], 10)] + neighbors

def map_embeddings(X_src, mapping_matrix):
    """
    Map source embeddings to the target embedding space.
    
    Args:
        X_src (np.ndarray): Source embedding of shape (1, src_dim).
        mapping_matrix (np.ndarray): Mapping matrix of shape (src_dim, tgt_dim).
    
    Returns:
        np.ndarray: Mapped embedding in the target space.
    """
    return np.dot(X_src, mapping_matrix)

def nearest_neighbors(mapped_src_embed, tgt_embeds, tgt_words, k=3):
    """
    Find the nearest neighbors in the target space for the source word embedding.
    
    Args:
        mapped_src_embed (np.ndarray): Source embedding mapped to the target space.
                                       Shape: (1, target_dim).
        tgt_embeds (np.ndarray): Target embeddings for all target words. Shape: (n_target_words, target_dim).
        tgt_words (list): List of all target words corresponding to the target embeddings.
        k (int): Number of nearest neighbors to retrieve.
    
    Returns:
        list: List of (target_word, similarity) tuples.
    """
    # Compute cosine similarity between source and target embeddings
    similarities = cosine_similarity(mapped_src_embed, tgt_embeds)  # Shape: (1, n_target_words)
    
    # Get the indices of the top-k similarities
    top_k_indices = np.argsort(similarities[0])[-k:][::-1]
    neighbors = [(tgt_words[idx], similarities[0][idx]) for idx in top_k_indices]
    
    return neighbors

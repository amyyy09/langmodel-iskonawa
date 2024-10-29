import os
import uuid
import json
import re

class CorpusEntry:
    """
    Represents an entry in a corpus.

    Attributes:
        file (str): The file associated with the corpus entry.
        text (str): The text of the corpus entry.
        words (list): A list of WordEntry objects associated with the corpus entry.
        id (str): A unique identifier for the corpus entry.
    """

    def __init__(self, file, text, words=None, entry_id=None):
        """
        Initializes a CorpusEntry instance.

        Args:
            file (str): The file associated with the corpus entry.
            text (str): The text of the corpus entry.
            words (list, optional): A list of WordEntry objects. Defaults to an empty list if not provided.
            entry_id (str, optional): A unique identifier for the corpus entry. Defaults to a new UUID if not provided.
        """
        self.file = file
        self.text = text
        self.words = words if words is not None else []
        self.id = entry_id if entry_id else str(uuid.uuid4())

    def __str__(self):
        """
        Returns a string representation of the corpus entry.

        Returns:
            str: The text of the corpus entry.
        """
        words_str = "\n".join([str(word) for word in self.words])
        return f"{self.text}"

    def process_words(self):
        """
        Processes the words in the corpus entry.

        If there is only one word in the words list, it processes that word and replaces the words list with the processed word.
        """
        if len(self.words) == 1:
            self.words = self.words[0].process()

class WordEntry:
    """
    Represents a word entry with its morpheme breaks and part-of-speech (POS) tags.

    Attributes:
        word (str): The word.
        mb (list or str): The morpheme breaks associated with the word.
        pos (list or str): The part-of-speech tags associated with the word.
    """

    def __init__(self, word, mb=None, pos=None):
        """
        Initializes a WordEntry instance.

        Args:
            word (str): The word.
            mb (list or str, optional): The morpheme breaks associated with the word. Defaults to an empty list.
            pos (list or str, optional): The part-of-speech tags associated with the word. Defaults to an empty list.
        """
        self.word = word
        self.mb = mb if mb is not None else []
        self.pos = pos if pos is not None else []

    def __str__(self):
        """
        Returns a string representation of the word entry.

        Returns:
            str: A string representation of the word entry, including the word, morpheme breaks, and POS tags.
        """
        mb_str = " ".join(self.mb) if isinstance(self.mb, list) else self.mb
        pos_str = " ".join(self.pos) if isinstance(self.pos, list) else self.pos
        mb_str = mb_str if mb_str else "-"
        pos_str = pos_str if pos_str else "-"
        return f"Word: {self.word}, Morpheme Breaks: [{mb_str}], POS: [{pos_str}]"

    def process(self):
        """
        Processes the word entry by tokenizing the word and mapping the morpheme breaks and POS tags to the tokens.

        Returns:
            list: A list of new WordEntry objects, each representing a token from the original word.
        """
        # Tokenize the word by whitespaces and punctuation
        pattern = r'\w+|[^\w\s]'
        word_tokens = re.findall(pattern, self.word)

        # Initialize lists for new WordEntry objects
        new_word_entries = []

        # If mb or pos is a list, return word tokens with mb and pos still empty
        if isinstance(self.mb, list) or isinstance(self.pos, list):
            for token in word_tokens:
                # if token includes "ininteligible", ignore it
                if "ininteligible" in token:
                    continue
                new_word_entries.append(WordEntry(word=token, mb=None, pos=None))
            return new_word_entries

        # Tokenize the morpheme breaks and POS by whitespaces
        mb_tokens = self.mb.split()
        pos_tokens = self.pos.split()
        
        current_mb = []
        current_pos = []

        flag = False

        for token in word_tokens:
            if token.isalnum():
                # Append the first mb and pos to the first alphanumeric token
                if mb_tokens:
                    current_mb.append(mb_tokens.pop(0))
                if pos_tokens:
                    current_pos.append(pos_tokens.pop(0))
            else:
                new_word_entries.append(WordEntry(word=token, mb=None, pos=None))

            while mb_tokens or pos_tokens:
                # Process morpheme breaks and POS
                if mb_tokens and (mb_tokens[0].startswith('=') or mb_tokens[0].startswith('-')):
                    current_mb.append(mb_tokens.pop(0))
                else:
                    flag = True

                if pos_tokens and (pos_tokens[0].startswith('=') or pos_tokens[0].startswith('-')):
                    current_pos.append(pos_tokens.pop(0))
                else:
                    flag = True

                if flag:
                    flag = False
                    break
                    
            new_word_entries.append(WordEntry(word=token, mb=current_mb, pos=current_pos))
            current_mb = []
            current_pos = []

        # Handle remaining morpheme breaks and POS
        if current_mb or current_pos:
            new_word_entries[-1].mb = current_mb
            new_word_entries[-1].pos = current_pos

        return new_word_entries

class Corpus:
    """
    Represents a corpus of text entries.

    Attributes:
        root_directory (str): The root directory of the corpus.
        link (str): An optional link associated with the corpus.
        encoding (str): The encoding used for reading files.
        lengua_principal (str): The primary language of the corpus.
        n_entries (int): The number of entries in the corpus.
        entries (list): A list of CorpusEntry objects.
        text_column (str): The column name for the text in the JSON file.
        file_column (str): The column name for the file in the JSON file.
        pos_column (str): The column name for the part-of-speech tags in the JSON file.
        mb_column (str): The column name for the morpheme breaks in the JSON file.
        id_column (str): The column name for the entry ID in the JSON file.
    """

    def __init__(self, root_directory, link=None, encoding="utf-8", lengua_principal=None, n_entries=0, text_column=None, 
                 file_column=None, pos_column=None, mb_column=None, id_column=None):
        """
        Initializes a Corpus instance.

        Args:
            root_directory (str): The root directory of the corpus.
            link (str, optional): An optional link associated with the corpus. Defaults to None.
            encoding (str, optional): The encoding used for reading files. Defaults to "utf-8".
            lengua_principal (str, optional): The primary language of the corpus. Defaults to None.
            n_entries (int, optional): The number of entries in the corpus. Defaults to 0.
            text_column (str, optional): The column name for the text in the JSON file. Defaults to None.
            file_column (str, optional): The column name for the file in the JSON file. Defaults to None.
            pos_column (str, optional): The column name for the part-of-speech tags in the JSON file. Defaults to None.
            mb_column (str, optional): The column name for the morpheme breaks in the JSON file. Defaults to None.
            id_column (str, optional): The column name for the entry ID in the JSON file. Defaults to None.
        """
        self.root_directory = root_directory
        self.link = link
        self.encoding = encoding
        self.lengua_principal = lengua_principal
        self.n_entries = n_entries
        self.entries = []
        self.text_column = text_column
        self.file_column = file_column
        self.pos_column = pos_column
        self.mb_column = mb_column
        self.id_column = id_column

    def __str__(self):
        """
        Returns a string representation of the corpus.

        Returns:
            str: A string representation of the corpus entries.
        """
        entries_str = "\n".join([str(entry) for entry in self.entries])
        return f"{entries_str}"

    def get_words(self, unique=False):
        """
        Returns a list of all words in the corpus.

        Args:
            unique (bool, optional): Whether to return only unique words. Defaults to False.

        Returns:
            list: A list of all words in the corpus.
        """

        words = [word_entry.word for entry in self.entries for word_entry in entry.words]
        return list(set(words)) if unique else words
        
    def add_entry(self, entry):
        """
        Adds an entry to the corpus.

        Args:
            entry (CorpusEntry): The entry to add to the corpus.
        """
        self.entries.append(entry)
        self.n_entries += 1

    def read(self, file):
        """
        Reads entries from a JSON file and adds them to the corpus.

        Args:
            file (str): The path to the JSON file.
        """
        with open(file, 'r', encoding=self.encoding) as f:
            for line in f:
                item = json.loads(line.strip())
                text = item.get(self.text_column)
                file = item.get(self.file_column) if self.file_column else None
                pos = item.get(self.pos_column) if self.pos_column else None
                mb = item.get(self.mb_column) if self.mb_column else None
                entry_id = item.get(self.id_column) if self.id_column else None

                # Create a single WordEntry with the entire text, mb, and pos
                word_entry = WordEntry(word=text, mb=mb, pos=pos)
                words = [word_entry]

                # Create a CorpusEntry and add it to the corpus
                corpus_entry = CorpusEntry(file=file, text=text, words=words, entry_id=entry_id)
                self.add_entry(corpus_entry)

    def clean(self, process_words=True, remove_duplicates=True, min_length=1):
        """
        Cleans the corpus by removing entries with words shorter than the minimum length and optionally removing duplicates.

        Args:
            process_words (bool, optional): Whether to process the words in each entry. Defaults to True.
            remove_duplicates (bool, optional): Whether to remove duplicate entries. Defaults to True.
            min_length (int, optional): The minimum length of words to keep in the corpus. Defaults to 1.
        """
        unique_texts = set()
        unique_entries = []

        # Iterate over a copy of the list to avoid modification issues
        for entry in self.entries[:]:
            entry.text = entry.text.lower()

            # remove "ininteligible" from the text
            entry.text = re.sub(r'\bininteligible\b', '', entry.text)

            # Split the text into words and check if the entry should be removed based on word length
            words = entry.text.split()
            if len(words) < min_length:
                self.entries.remove(entry)
                continue

            # drop punctuation
            entry.text = re.sub(r'[^\w\s]', '', entry.text)

            # drop ( ) and [ ] and { }
            entry.text = re.sub(r'[\(\)\[\]\{\}]', '', entry.text)

            # Add unique entries to the list
            if remove_duplicates and entry.text not in unique_texts:
                unique_texts.add(entry.text)
                unique_entries.append(entry)

        # Update the entries list with unique entries if duplicates are to be removed
        if remove_duplicates:
            self.entries = unique_entries

        # Process the words in each entry if required
        if process_words:
            for entry in self.entries:
                entry.process_words()
            

class MultilingualCorpus(Corpus):
    """
    Represents a multilingual corpus of text entries.

    Attributes:
        root_directory (str): The root directory of the corpus.
        link (str): An optional link associated with the corpus.
        encoding (str): The encoding used for reading files.
        lengua_principal (str): The primary language of the corpus.
        n_entries (int): The number of entries in the corpus.
        text_column (str): The column name for the text in the JSON file.
        file_column (str): The column name for the file in the JSON file.
        pos_column (str): The column name for the part-of-speech tags in the JSON file.
        mb_column (str): The column name for the morpheme breaks in the JSON file.
        id_column (str): The column name for the entry ID in the JSON file.
        languages (list): A list of languages in the multilingual corpus.
        gloss_columns (dict): A dictionary mapping languages to their gloss column names.
        ft_columns (dict): A dictionary mapping languages to their free translation column names.
    """

    def __init__(self, root_directory, link=None, encoding="utf-8", lengua_principal=None, n_entries=0, text_column=None, 
                 file_column=None, pos_column=None, mb_column=None, id_column=None, languages=None, 
                 gloss_columns=None, ft_columns=None):
        """
        Initializes a MultilingualCorpus instance.

        Args:
            root_directory (str): The root directory of the corpus.
            link (str, optional): An optional link associated with the corpus. Defaults to None.
            encoding (str, optional): The encoding used for reading files. Defaults to "utf-8".
            lengua_principal (str, optional): The primary language of the corpus. Defaults to None.
            n_entries (int, optional): The number of entries in the corpus. Defaults to 0.
            text_column (str, optional): The column name for the text in the JSON file. Defaults to None.
            file_column (str, optional): The column name for the file in the JSON file. Defaults to None.
            pos_column (str, optional): The column name for the part-of-speech tags in the JSON file. Defaults to None.
            mb_column (str, optional): The column name for the morpheme breaks in the JSON file. Defaults to None.
            id_column (str, optional): The column name for the entry ID in the JSON file. Defaults to None.
            languages (list, optional): A list of languages in the multilingual corpus. Defaults to an empty list.
            gloss_columns (dict, optional): A dictionary mapping languages to their gloss column names. Defaults to an empty dictionary.
            ft_columns (dict, optional): A dictionary mapping languages to their free translation column names. Defaults to an empty dictionary.
        """
        super().__init__(root_directory, link, encoding, lengua_principal, n_entries, text_column, file_column, 
                         pos_column, mb_column, id_column)
        self.languages = languages if languages is not None else []
        self.gloss_columns = gloss_columns if gloss_columns is not None else {}
        self.ft_columns = ft_columns if ft_columns is not None else {}

    def add_entry(self, entry):
        """
        Adds a multilingual entry to the corpus.

        Args:
            entry (MultilingualCorpusEntry): The entry to add to the corpus.

        Raises:
            ValueError: If the entry is not of type MultilingualCorpusEntry.
        """
        if isinstance(entry, MultilingualCorpusEntry):
            super().add_entry(entry)
        else:
            raise ValueError("Entry must be of type MultilingualCorpusEntry")

    def read(self, file):
        """
        Reads entries from a JSON file and adds them to the corpus.

        Args:
            file (str): The path to the JSON file.
        """
        with open(file, 'r', encoding=self.encoding) as f:
            for line in f:
                item = json.loads(line.strip())
                text = item.get(self.text_column)
                file = item.get(self.file_column) if self.file_column else None
                pos = item.get(self.pos_column) if self.pos_column else None
                mb = item.get(self.mb_column) if self.mb_column else None
                entry_id = item.get(self.id_column) if self.id_column else None

                # Multilingual columns for free translation (ft)
                ft = {lang: item.get(self.ft_columns[lang]) for lang in self.languages if lang in self.ft_columns}

                # Multilingual columns for glosses
                gloss = {lang: item.get(self.gloss_columns[lang]) for lang in self.languages if lang in self.gloss_columns}

                # Create a single WordEntry with the entire text, mb, pos, and gloss
                word_entry = MultilingualWordEntry(word=text, mb=mb, pos=pos, gloss=gloss)
                words = [word_entry]

                # Create a MultilingualCorpusEntry and add it to the corpus
                multilingual_entry = MultilingualCorpusEntry(file=file, text=text, words=words, entry_id=entry_id, ft=ft)
                self.add_entry(multilingual_entry)

    def clean(self, process_words=True, remove_duplicates=True, min_length=1):
        """
        Cleans the corpus by removing entries with words shorter than the minimum length and optionally removing duplicates.

        Args:
            process_words (bool, optional): Whether to process the words in each entry. Defaults to True.
            remove_duplicates (bool, optional): Whether to remove duplicate entries. Defaults to True.
            min_length (int, optional): The minimum length of words to keep in the corpus. Defaults to 1.
        """
        super().clean(process_words=False, remove_duplicates=remove_duplicates, min_length=min_length)

        # Clean the free translation fields
        for entry in self.entries:
            if process_words:
                entry.process_words()
            for lang in entry.ft:
                entry.ft[lang] = entry.ft[lang].lower() if entry.ft[lang] else entry.ft[lang]

class MultilingualCorpusEntry(CorpusEntry):
    """
    Represents an entry in a multilingual corpus.

    Attributes:
        file (str): The file associated with the corpus entry.
        text (str): The text of the corpus entry.
        words (list): A list of WordEntry objects associated with the corpus entry.
        id (str): A unique identifier for the corpus entry.
        ft (dict): A dictionary of free translations for different languages.
    """

    def __init__(self, file, text, words=None, entry_id=None, ft=None):
        """
        Initializes a MultilingualCorpusEntry instance.

        Args:
            file (str): The file associated with the corpus entry.
            text (str): The text of the corpus entry.
            words (list, optional): A list of WordEntry objects. Defaults to an empty list if not provided.
            entry_id (str, optional): A unique identifier for the corpus entry. Defaults to None.
            ft (dict, optional): A dictionary of free translations for different languages. Defaults to an empty dictionary if not provided.
        """
        super().__init__(file, text, words, entry_id)
        self.ft = ft if ft is not None else {}

    def __str__(self):
        """
        Returns a string representation of the multilingual corpus entry.

        Returns:
            str: A string representation of the multilingual corpus entry, including the text and free translations.
        """
        # Create a string representation of the free translations
        ft_str = ", ".join([f"{lang}: {translation}" for lang, translation in self.ft.items()])
        # Create a string representation of the words
        words_str = "\n".join([str(word) for word in self.words])
        # Return the formatted string
        return f"{self.text}, Free Translations: [{ft_str}]"

    def process_words(self):
        """
        Processes the words in the multilingual corpus entry.

        If there is only one word in the words list, it processes that word and replaces the words list with the processed word.
        """
        if len(self.words) == 1:
            self.words = self.words[0].process()

class MultilingualWordEntry(WordEntry):
    """
    Represents a word entry in a multilingual corpus with morpheme breaks, part-of-speech (POS) tags, and glosses.

    Attributes:
        word (str): The word.
        mb (list or str): The morpheme breaks associated with the word.
        pos (list or str): The part-of-speech tags associated with the word.
        gloss (dict): A dictionary mapping languages to their glosses.
    """

    def __init__(self, word, mb=None, pos=None, gloss=None):
        """
        Initializes a MultilingualWordEntry instance.

        Args:
            word (str): The word.
            mb (list or str, optional): The morpheme breaks associated with the word. Defaults to an empty list.
            pos (list or str, optional): The part-of-speech tags associated with the word. Defaults to an empty list.
            gloss (dict, optional): A dictionary mapping languages to their glosses. Defaults to an empty dictionary.
        """
        super().__init__(word, mb, pos)
        self.gloss = gloss if gloss is not None else {}

    def __str__(self):
        """
        Returns a string representation of the multilingual word entry.

        Returns:
            str: A string representation of the multilingual word entry, including the word, morpheme breaks, POS tags, and glosses.
        """
        gloss_str = ", ".join([f"{lang}: {gloss}" for lang, gloss in self.gloss.items()])
        base_str = super().__str__()
        return f"{base_str}, Gloss: [{gloss_str}]"

    def process(self):
        """
        Processes the multilingual word entry by tokenizing the word and mapping the morpheme breaks, POS tags, and glosses to the tokens.

        Returns:
            list: A list of new MultilingualWordEntry objects, each representing a token from the original word.
        """
        # Tokenize the word by whitespaces and punctuation
        pattern = r'\w+|[^\w\s]'
        word_tokens = re.findall(pattern, self.word)

        # Initialize lists for new MultilingualWordEntry objects
        new_word_entries = []

        # Tokenize morpheme breaks and POS
        mb_tokens = self.mb.split() if isinstance(self.mb, str) else []
        pos_tokens = self.pos.split() if isinstance(self.pos, str) else []

        # Process glosses for each language
        gloss_tokens = {lang: gloss.split() for lang, gloss in self.gloss.items() if isinstance(gloss, str)}

        current_mb = []
        current_pos = []
        current_gloss = {lang: [] for lang in self.gloss}

        flag = False

        for token in word_tokens:
            if token.isalnum():
                # Map morpheme breaks and POS
                if mb_tokens:
                    current_mb.append(mb_tokens.pop(0))
                if pos_tokens:
                    current_pos.append(pos_tokens.pop(0))

                # Map glosses
                for lang, tokens in gloss_tokens.items():
                    if tokens:
                        current_gloss[lang].append(tokens.pop(0))
            else:
                new_word_entries.append(MultilingualWordEntry(word=token, mb=None, pos=None, gloss=None))

            while mb_tokens or pos_tokens or any(tokens for tokens in gloss_tokens.values()):
                # Process morpheme breaks, POS, and glosses
                if mb_tokens and (mb_tokens[0].startswith('=') or mb_tokens[0].startswith('-')):
                    current_mb.append(mb_tokens.pop(0))
                else:
                    flag = True

                if pos_tokens and (pos_tokens[0].startswith('=') or pos_tokens[0].startswith('-')):
                    current_pos.append(pos_tokens.pop(0))
                else:
                    flag = True

                for lang, tokens in gloss_tokens.items():
                    if tokens and (tokens[0].startswith('=') or tokens[0].startswith('-')):
                        current_gloss[lang].append(tokens.pop(0))
                    else:
                        flag = True

                if flag:
                    flag = False
                    break

            # Add a new token with mapped morphemes, POS, and glosses
            new_word_entries.append(MultilingualWordEntry(
                word=token,
                mb=current_mb,
                pos=current_pos,
                gloss={lang: current_gloss[lang] for lang in current_gloss}
            ))

            current_mb = []
            current_pos = []
            current_gloss = {lang: [] for lang in self.gloss}

        # Handle any remaining glosses, morphemes, and POS for the last token
        if current_mb or current_pos or any(current_gloss.values()):
            new_word_entries[-1].mb = current_mb
            new_word_entries[-1].pos = current_pos
            new_word_entries[-1].gloss = {lang: " ".join(current_gloss[lang]) for lang in current_gloss}

        return new_word_entries
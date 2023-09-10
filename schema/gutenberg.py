"""
Defines the database schema in Weaviate for storing hierarchical data from Project Gutenberg.
Books are at the top of the hierarchy, followed by chapters, followed by paragraphs.
Each entry is linked to its parent and child via a two-way reference.

As of Weaviate 1.21.1, the use of two-way references is to enable semantic search
and generative results on the Paragraph's texts (crucial for the Q&A capability of erudite)
while using the referenced parent's properties for the purpose of filtering, grouping and 
offsetting.

This might change in the future when nested classes are supported (planned for Weaviate 1.22).
See https://weaviate.io/developers/weaviate/roadmap for details on the roadmap.

{Book}
    title: str
    authors: List[str]
    meta: Meta
    chapter: Chapter

{Meta}
    language: str
    source: str
    citation: str
    containedIn: Book

{Chapter}
    title: (Optional) str
    seq: int
    text: str
    paragraphs: List[Paragraph]
    containedIn: Book

{Paragraph}
    seq: int
    text: str
    containedIn: Chapter

"""

class_book = {
    "class": "Book",
    "moduleConfig": {
        "text2vec-openai": {
            "skip": False,
            "vectorizeClassName": False,
            "vectorizePropertyName": False,
        },
        "generative-openai": {},
    },
    "properties": [
        {
            "name": "title",
            "dataType": ["text"],
            "description": "The title of the book.",
        },
        {
            "name": "author",
            "dataType": ["text[]"],
            "description": "The name of the author.",
        },
        {
            "name": "meta",
            "dataType": ["Meta"],
            "description": "Metadata on the origin, language and subject of the book.",
        },
        {"name": "chapters", "dataType": ["Chapter"]},
    ],
    "vectorizer": "text2vec-openai",
}

class_meta = {
    "class": "Meta",
    "moduleConfig": {
        "text2vec-openai": {
            "skip": False,
            "vectorizeClassName": False,
            "vectorizePropertyName": False,
        },
        "generative-openai": {},
    },
    "properties": [
        {
            "name": "language",
            "dataType": ["text"],
            "description": "The language of the book.",
        },
        {
            "name": "subject",
            "dataType": ["text"],
            "description": "The subject of the book.",
        },
        {
            "name": "citation",
            "dataType": ["text"],
            "description": "Project Gutenberg citation.",
        },
        {
            "name": "containedIn",
            "dataType": ["Book"],
            "description": "The Book that contains this Meta.",
        },
    ],
    "vectorizer": "text2vec-openai",
}

class_chapter = {
    "class": "Chapter",
    "moduleConfig": {
        "text2vec-openai": {
            "skip": False,
            "vectorizeClassName": False,
            "vectorizePropertyName": False,
        },
        "generative-openai": {},
        "qna-openai": {},
    },
    "properties": [
        {
            "name": "title",
            "dataType": ["text"],
            "description": "(Optional) The name of the chapter.",
        },
        {
            "name": "seq",
            "dataType": ["int"],
            "description": "The order in which this chapter appears within the book.",
        },
        {
            "name": "text",
            "dataType": ["text"],
            "moduleConfig": {"text2vec-openai": {"skip": True}},
            "description": "The text of the whole chapter.",
        },
        {
            "name": "paragraphs",
            "dataType": ["Paragraph"],
            "description": "The paragraphs under the chapter",
        },
        {
            "name": "containedIn",
            "dataType": ["Book"],
            "description": "The Book that contains this Chapter.",
        },
    ],
    "vectorizer": "text2vec-openai",
}

class_paragraph = {
    "class": "Paragraph",
    "moduleConfig": {
        "text2vec-openai": {
            "skip": False,
            "vectorizeClassName": False,
            "vectorizePropertyName": False,
        },
        "generative-openai": {},
        "qna-openai": {"model": "text-davinci-002"},
    },
    "properties": [
        {
            "name": "seq",
            "dataType": ["int"],
            "description": "Denotes the order in which this paragraph appears within the chapter.",
        },
        {
            "name": "text",
            "dataType": ["text"],
            "description": "The text of the whole paragraph.",
        },
        {
            "name": "containedIn",
            "dataType": ["Chapter"],
            "description": "The Chapter that contains this paragraph.",
        },
    ],
    "vectorizer": "text2vec-openai",
}

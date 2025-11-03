# FileIntel API - Verified Request/Response Formats

**Verified Date**: 2025-10-25
**FileIntel Instance**: http://localhost:8000
**API Version**: 2.0
**Test Collection**: thesis_sources (agile/product development)

---

## Summary of Changes from Original Documentation

### ✅ CORRECTED Information

1. **Query Endpoint Path**:
   - ❌ Old: `POST /v2/queries`
   - ✅ Actual: `POST /api/v2/collections/{collection_name}/query`

2. **Request Body Field**:
   - ❌ Old: `"query": "..."`
   - ✅ Actual: `"question": "..."`

3. **Metadata Availability**:
   - ✅ **GOOD NEWS**: Document metadata is included in query responses!
   - Each source includes `document_metadata` with authors, title, year, etc.
   - No need for separate metadata fetches in most cases

4. **Citation Format**:
   - ✅ FileIntel provides pre-formatted `in_text_citation` field
   - ✅ FileIntel provides `citation` field for bibliography
   - Example: `"in_text_citation": "(Schmidt, 2018, p. 95)"`

---

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Request**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "ok",
  "timestamp": 1761399132.3839493
}
```

---

### 2. List Collections

**Endpoint**: `GET /api/v2/collections`

**Request**:
```bash
curl http://localhost:8000/api/v2/collections
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "1d5b28a7-0522-4c7b-99f3-99b2794d9a15",
      "name": "thesis_sources",
      "description": null,
      "status": "processing"
    }
  ],
  "error": null,
  "timestamp": "2025-10-25T13:32:21.034891",
  "api_version": "2.0"
}
```

**Fields**:
- `id` (UUID): Unique collection identifier
- `name` (string): Collection name used in queries
- `description` (string|null): Optional description
- `status` (string): `"processing"` | `"ready"` | other states

---

### 3. Vector RAG Query

**Endpoint**: `POST /api/v2/collections/{collection_name}/query`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v2/collections/thesis_sources/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is agile development?",
    "rag_type": "vector"
  }'
```

**Request Body Schema**:
```json
{
  "question": "string (required) - The query question",
  "rag_type": "string (optional) - 'vector' | 'graph' | 'auto' (default: auto)",
  "max_sources": "integer (optional) - Maximum number of sources to return"
}
```

**Important Notes**:
- Use `"rag_type": "vector"` for collections without GraphRAG indexing
- Field is `question`, not `query`!
- Path uses collection name, not ID

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "answer": "string - Generated answer with inline citations",
    "sources": [ /* array of source objects */ ],
    "query_type": "vector",
    "routing_explanation": "string - Why this query type was chosen",
    "collection_id": "uuid",
    "question": "string - Echo of the question",
    "processing_time_ms": 18969
  },
  "error": null,
  "timestamp": "2025-10-25T13:33:21.447586",
  "api_version": "2.0"
}
```

---

### 4. Source Object Schema

Each source in the `sources` array has this structure:

```json
{
  "document_id": "uuid - Document identifier",
  "chunk_id": "uuid - Specific chunk identifier",
  "filename": "string - Original filename",

  // PRE-FORMATTED CITATIONS (ready to use!)
  "citation": "string - Full citation for bibliography",
  "in_text_citation": "string - Short form for inline citation",

  // CHUNK CONTENT
  "text": "string - Excerpt from the document (truncated)",

  // RELEVANCE SCORES
  "similarity_score": 0.7913585429573942,
  "relevance_score": 0.7913585429573942,
  "distance": 0.20864145704260584,
  "position": 1980,

  // CHUNK METADATA
  "chunk_metadata": {
    "source": "string - Internal file path",
    "page_number": 980,
    "extraction_method": "string - How it was extracted",
    "backend": "string",
    "format": "string",
    "element_count": 7,
    "element_types": { "text": 7 },
    "has_coordinates": true,
    "coordinate_coverage": 1.0,
    "chunk_strategy": "string",
    "chunk_type": "vector"
  },

  // DOCUMENT METADATA (the gold for citations!)
  "document_metadata": {
    "title": "string - Full document title",
    "authors": ["string array - Full author names"],
    "author_surnames": ["string array - Just surnames"],
    "publication_date": "string - Year or version",
    "language": "string",
    "document_type": "string - Guide|Report|Book|etc",

    // OPTIONAL FIELDS (may not be present)
    "abstract": "string (optional)",
    "keywords": ["string array (optional)"],
    "publisher": "string (optional)",
    "source_url": "string (optional)",
    "harvard_citation": "string (optional) - Pre-formatted Harvard style!",

    // EXTRACTION INFO
    "llm_extracted": true,
    "extraction_method": "llm_analysis",

    // FILE INFO
    "file_path": "string - Internal path",
    "uploaded_via": "api_v2",
    "original_filename": "string"
  }
}
```

---

### 5. Example Source Objects

#### Example 1: SEBoK Guide (No Year)
```json
{
  "document_id": "5f62cc19-bd6a-47ff-96bd-df44cd28089d",
  "filename": "Guide_to_the_Systems_Engineering_Body_of_Knowledge_v2.10.pdf",
  "citation": "Guide to the Systems Engineering Body of Knowledge (SEBoK), (2.10), 'Guide to the Systems Engineering Body of Knowledge (SEBoK) Version 2.10'",
  "in_text_citation": "(SEBoK, 2.10, p. 980)",
  "text": "16. Agile development processes are increasingly used...",
  "similarity_score": 0.7913585429573942,
  "chunk_metadata": {
    "page_number": 980
  },
  "document_metadata": {
    "title": "Guide to the Systems Engineering Body of Knowledge (SEBoK) Version 2.10",
    "authors": ["Guide to the Systems Engineering Body of Knowledge (SEBoK)"],
    "author_surnames": ["SEBoK"],
    "publication_date": "2.10",
    "document_type": "Guide",
    "source_url": "www.sebokwiki.org"
  }
}
```

#### Example 2: Academic Paper (Proper Citation)
```json
{
  "document_id": "a8d9cee0-2320-4a69-9997-dbfa86f344ff",
  "filename": "Agile Development of Physical Products.pdf",
  "citation": "Tobias Sebastian Schmidt, (2018), 'Agile Development of Physical Products: An Empirical Study about Motivations, Potentials and Applicability'",
  "in_text_citation": "(Schmidt, 2018, p. 95)",
  "text": "• Agile software development is a more mature concept...",
  "similarity_score": 0.7846584916114807,
  "chunk_metadata": {
    "page_number": 95
  },
  "document_metadata": {
    "title": "Agile Development of Physical Products: An Empirical Study about Motivations, Potentials and Applicability",
    "authors": [
      "Tobias Sebastian Schmidt",
      "Stefan Weiss",
      "Kristin Paetzold"
    ],
    "author_surnames": ["Schmidt", "Weiss", "Paetzold"],
    "publication_date": "2018",
    "publisher": "Universität der Bundeswehr München",
    "document_type": "Report",
    "harvard_citation": "Schmidt, T. S., Weiss, S., & Paetzold, K. (2018). Agile Development of Physical Products: An Empirical Study about Motivations, Potentials and Applicability. Universität der Bundeswehr München."
  }
}
```

#### Example 3: Book (Multiple Authors)
```json
{
  "document_id": "f49d6e43-c91b-40bd-85aa-97f19d84b37a",
  "filename": "Scrum_ The Complete Guide to the Agile Project Manaork & Solve Problems in Half the Time - Josh Wright.pdf",
  "citation": "Josh Wright, (2020), 'Scrum: the complete guide to the agile project management framework...'",
  "in_text_citation": "(Wright, 2020, p. 92)",
  "chunk_metadata": {
    "page_number": 92
  },
  "document_metadata": {
    "title": "Scrum: the complete guide to the agile project management framework that helps the software development lean team to efficiently structure and simplify the work & solve problems in half the time",
    "authors": ["Josh Wright"],
    "author_surnames": ["Wright"],
    "publication_date": "2020",
    "publisher": "Josh Wright",
    "document_type": "book",
    "language": "English"
  }
}
```

---

### 6. Document Metadata Endpoint (Optional)

**Endpoint**: `GET /api/v2/metadata/document/{document_id}`

**When to use**:
- If you need metadata for a specific document
- For batch operations where you already have document IDs
- **Usually NOT needed** since query responses include metadata!

**Request**:
```bash
curl http://localhost:8000/api/v2/metadata/document/a8d9cee0-2320-4a69-9997-dbfa86f344ff
```

**Response**:
```json
{
  "success": true,
  "data": {
    "document_id": "a8d9cee0-2320-4a69-9997-dbfa86f344ff",
    "filename": "Agile Development of Physical Products.pdf",
    "has_extracted_metadata": true,
    "metadata": {
      "title": "...",
      "authors": [...],
      "publication_date": "2018",
      // ... same structure as document_metadata above
    },
    "created_at": "2025-10-23T19:04:43.136491Z",
    "updated_at": "2025-10-23T23:55:33.278583Z"
  },
  "error": null,
  "timestamp": "2025-10-25T13:34:46.153894",
  "api_version": "2.0"
}
```

---

## Sample Answer Format

The `answer` field contains prose with **inline citations already formatted**:

```
Agile development is a widely used and growing approach to software development
[SEBoK, 2.10, p. 980]. It's considered a more mature concept, having been applied
in the software industry for about two decades [Schmidt, 2018, p. 95].

Here's a breakdown of what defines agile development, based on the provided sources:

*   **Iterative and Incremental:** Agile development proceeds iteratively in cycles
    that produce incremental versions of software [SEBoK, 2.10, p. 980].
*   **Team Structure:** Agile teams are typically small and closely coordinated
    [SEBoK, 2.10, p. 980]. They are self-organizing and cross-functional [Golder].
*   **Adaptive and Flexible:** Agile promotes adaptive planning, evolutionary
    development and delivery, and encourages rapid and flexible response to change
    [Golder].
```

**Key Observations**:
- Citations are in `[Author, Year, p.X]` format
- Some citations lack page numbers: `[Golder]`
- Citations are placed where evidence supports claims
- Answer includes structured formatting (bullet points, headings)

---

## Implementation Implications for AcadWrite

### ✅ RESOLVED Issues

1. **Citation Metadata Availability** ✅
   - **Resolution**: Metadata IS included in query responses
   - No need for separate metadata API calls
   - Can generate proper citations directly from query results

2. **Citation Format** ✅
   - **Resolution**: FileIntel provides pre-formatted citations
   - `in_text_citation`: Ready-to-use inline format
   - `citation`: Ready-to-use bibliography format
   - Can use these directly or transform to other styles

3. **API Endpoint Paths** ✅
   - **Resolution**: Documented correct paths
   - Use collection name in path: `/api/v2/collections/{name}/query`
   - Request body uses `question` field

### 🔧 Design Decisions

#### Decision: How to Handle Citations?

**Recommended Approach**: **Hybrid Strategy**

1. **Use FileIntel's inline citations as-is** for the answer text
   - Advantage: Already correctly placed by LLM
   - Format: `[Author, Year, p.X]`

2. **Generate bibliography from sources array**
   - Use `citation` field for each source
   - Or transform `document_metadata` to desired format

3. **Optional: Convert inline format**
   - Transform `[Author, Year, p.X]` to footnotes `[^1]`
   - Build footnote list from sources
   - Allow users to choose citation style

#### Decision: Citation Placement Strategy

**Recommended**: **Trust FileIntel's Placement**

FileIntel's answer already includes citations where relevant:
- No need for citation placement algorithm
- No need for LLM post-processing
- Just need format conversion if user wants footnotes instead of inline

**Conversion Algorithm**:
```python
# If user wants footnotes instead of inline:
1. Parse answer text for citation patterns: [Author, Year, p.X]
2. Match each citation to corresponding source
3. Replace with footnote marker: [^N]
4. Generate footnote list at bottom
```

#### Decision: Metadata Handling

**Recommended**: **Use Embedded Metadata**

- Don't call separate metadata endpoint
- Extract from `document_metadata` in each source
- Handle missing fields gracefully (some sources lack year, publisher, etc.)

**Fallback for Missing Metadata**:
```python
if source.document_metadata.publication_date:
    year = source.document_metadata.publication_date
else:
    year = "n.d."  # No date

if source.document_metadata.authors:
    author = source.document_metadata.authors[0]
else:
    author = source.filename  # Fallback to filename
```

---

## Updated Data Models for AcadWrite

### Source Model
```python
from pydantic import BaseModel
from typing import Optional, List

class ChunkMetadata(BaseModel):
    page_number: Optional[int] = None
    extraction_method: Optional[str] = None
    # ... other fields as needed

class DocumentMetadata(BaseModel):
    title: str
    authors: List[str] = []
    author_surnames: List[str] = []
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None
    harvard_citation: Optional[str] = None
    # ... other optional fields

class Source(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    citation: str  # Pre-formatted bibliography citation
    in_text_citation: str  # Pre-formatted inline citation
    text: str  # Chunk content
    similarity_score: float
    relevance_score: float
    chunk_metadata: ChunkMetadata
    document_metadata: DocumentMetadata

class QueryResponse(BaseModel):
    answer: str  # Already includes inline citations!
    sources: List[Source]
    query_type: str  # "vector" | "graph" | "hybrid"
    routing_explanation: Optional[str] = None
    collection_id: str
    question: str
    processing_time_ms: int
```

---

## API Client Implementation Guide

### Basic Query Example
```python
import httpx
from typing import Optional

class FileIntelClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query(
        self,
        collection: str,
        question: str,
        rag_type: str = "vector",
        max_sources: Optional[int] = None
    ) -> QueryResponse:
        """Query FileIntel with vector RAG"""
        url = f"{self.base_url}/api/v2/collections/{collection}/query"

        payload = {
            "question": question,
            "rag_type": rag_type
        }
        if max_sources:
            payload["max_sources"] = max_sources

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        if not data["success"]:
            raise FileIntelError(data.get("error", "Unknown error"))

        return QueryResponse(**data["data"])

    async def health_check(self) -> bool:
        """Check if FileIntel is available"""
        response = await self.client.get(f"{self.base_url}/health")
        data = response.json()
        return data.get("status") == "ok"

    async def list_collections(self) -> List[dict]:
        """List available collections"""
        response = await self.client.get(f"{self.base_url}/api/v2/collections")
        data = response.json()
        return data["data"]
```

---

## Testing Checklist

- [x] Health endpoint responds
- [x] Collections list endpoint works
- [x] Vector query returns proper response
- [x] All sources include document_metadata
- [x] Citations are pre-formatted
- [x] Page numbers are available
- [x] Metadata endpoint works for individual documents
- [ ] Error handling for invalid collection
- [ ] Error handling for malformed queries
- [ ] Rate limiting behavior (if any)

---

## Error Response Format

**Expected Error Response**:
```json
{
  "success": false,
  "data": null,
  "error": "Error message describing what went wrong",
  "timestamp": "2025-10-25T13:34:46.153894",
  "api_version": "2.0"
}
```

**Common HTTP Status Codes**:
- `200`: Success (check `success` field in body)
- `404`: Collection not found or endpoint doesn't exist
- `422`: Validation error (invalid request body)
- `500`: Internal server error

---

## Notes for Implementation

1. **No N+1 Query Problem**: Metadata is already in query response, no extra calls needed!

2. **Citation Styles**: FileIntel uses inline `[Author, Year, p.X]` format. AcadWrite can:
   - Keep this format (easiest)
   - Convert to footnotes (requires parsing)
   - Use the pre-formatted `citation` field for bibliography

3. **Page Numbers**: Always available in `chunk_metadata.page_number`

4. **Harvard Citations**: Some documents include pre-formatted `harvard_citation` - use if available!

5. **Missing Data**: Handle gracefully when:
   - `publication_date` is missing or weird (e.g., "2.10" for versions)
   - `authors` is empty
   - `publisher` is missing

6. **Collection Status**: Check `status` field - if still "processing", documents might not all be indexed yet

---

## Conclusion

**Major Wins**:
- ✅ Metadata IS available in query responses
- ✅ Citations are pre-formatted and ready to use
- ✅ No need for complex citation placement algorithms
- ✅ API structure is logical and well-designed

**What AcadWrite Needs to Do**:
1. Parse FileIntel's response correctly
2. Optionally convert citation format (inline → footnotes)
3. Generate bibliography from sources
4. Handle missing metadata fields gracefully

The path forward is much clearer than the original planning documents suggested!

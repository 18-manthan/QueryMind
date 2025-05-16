import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pgvector.sqlalchemy import Vector
import numpy as np

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    """Document model for storing metadata about ingested PDFs."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    total_pages = Column(Integer, nullable=False)
    upload_timestamp = Column(String, default=func.now())
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """Document chunk model for storing text passages and embeddings."""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI embeddings are 1536 dimensions
    
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


def init_db():
    """Initialize the database schemas."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def store_document(filename, total_pages):
    """Store a new document in the database."""
    db = SessionLocal()
    try:
        document = Document(filename=filename, total_pages=total_pages)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    finally:
        db.close()


def store_chunk(document_id, text, chunk_index, page_number, embedding):
    """Store a document chunk with its embedding."""
    db = SessionLocal()
    try:
        chunk = DocumentChunk(
            document_id=document_id,
            text=text,
            chunk_index=chunk_index,
            page_number=page_number,
            embedding=embedding
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    finally:
        db.close()


def semantic_search(query_embedding, limit=5):
    """Perform semantic search against document chunks."""
    db = SessionLocal()
    try:
        # Convert the query embedding to a numpy array if it's not already
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = np.array(query_embedding)
            
        # Perform the cosine similarity search
        chunks = db.query(DocumentChunk).order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
        
        return chunks
    finally:
        db.close()


def get_document_details(document_id):
    """Get document details by ID."""
    db = SessionLocal()
    try:
        return db.query(Document).filter(Document.id == document_id).first()
    finally:
        db.close() 
#!/usr/bin/env python3

import json
import time
import os
import ebooklib

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

from concurrent.futures import ThreadPoolExecutor, as_completed
from ebooklib import epub
from bs4 import BeautifulSoup

from haystack import Document
from haystack.components.converters import PyPDFToDocument, DOCXToDocument

from collections import Counter
from dataclasses import replace

from .cleaner import DocumentCleaner
from .helpers.helper_get_subject_name import infer_subject
from .helpers.helper_get_grade_name import infer_grade
from .helpers.helper_ocr import repair_pdf_text

load_dotenv()

document_path = Path(__file__).parent.parent.parent/"ressources"/"books_to_chunk"/"programming"



class Converter:
    def __init__(self):
        self.__pdf_converter = PyPDFToDocument()
        self.__docx_converter = DOCXToDocument()
        self.__cleaner = DocumentCleaner()
        self.__documents = []
    def check_file_type(self, items:Path):
        return Counter(
            f.suffix.lower() for f in items.rglob("*") if f.is_file()
            )

    def convert_epub(self, file_path: Path):
        book = epub.read_epub(str(file_path))

        text = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text.append(soup.get_text(separator="\n"))

        return [
            Document(
                content="\n".join(text),
                meta={
                    "date_added": datetime.now(timezone.utc).isoformat(),
                    "file_name": file_path.name,
                    "subject": infer_subject(file_path),
                    "grade": infer_grade(file_path),
                },
            )
        ]

    def convert_files(self, file_path) -> list:
        """
        This function convert document of direct extension to haystack documents
        """
        meta={
            "date_added":datetime.now(timezone.utc).isoformat(),
            "file_name":file_path.name,
            "subject":infer_subject(file_path),
            "grade":infer_grade(file_path)
            }

        if file_path.suffix.lower() == ".pdf":
            documents = self.__pdf_converter.run(
                sources=[file_path],
                meta=meta
            )["documents"]
            documents = [
                replace(doc, content=repair_pdf_text(file_path, doc.content))
                for doc in documents
            ]
        elif file_path.suffix.lower() == ".docx":
            documents = self.__docx_converter.run(
                sources=[file_path],
                meta=meta
            )["documents"]
        elif file_path.suffix.lower() == ".epub":
            documents = self.convert_epub(file_path=file_path)
        else:
            return []
        
        clean_docs = []
        for doc in documents:
            clean_docs.append(
                replace(doc, 
                        content=self.__cleaner.clean_text(doc.content)
                        )
                )

        return clean_docs

    def convert_doc_parallel(self,
                             items:Path,
                             nbr_worker=int(os.getenv("MAX_WORKERS", 3))
                             ):
        """run operation in parallel with threadexecutor"""
        start_time = time.perf_counter()
        print("Process started")
        files = [file for file in items.rglob("*") if file.suffix.lower() in (".pdf",".docx", ".epub")]
        
        with ThreadPoolExecutor(max_workers=nbr_worker) as executor:
            futures_conversion = [executor.submit(self.convert_files, file) for file in files]

            for i, document in enumerate(as_completed(futures_conversion), start=1):
                docs = document.result()
                self.__documents.extend(docs)
                print(f"document {i} over {len(futures_conversion)} converted")
        end_time = time.perf_counter()
        elaps = end_time - start_time

        with open("document_split.json", "w", encoding="utf-8") as file:
            json.dump([doc.to_dict() for doc in self.__documents], file, indent=2)

        print(f"process complete after {elaps:.2f} seconds")
        return self.__documents

if __name__ == "__main__":
    test_conversion = Converter()
    document_path = Path(__file__).parent.parent.parent/"ressources"
    #print(test_conversion.check_file_type(items=document_path))
    print(test_conversion.convert_doc_parallel(items=document_path))
    #print(test_conversion.load_ressources())
    #print(await test_conversion.load_ressources())

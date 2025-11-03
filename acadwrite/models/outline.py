"""Data models for document outlines."""

import re
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class OutlineItem(BaseModel):
    """A single item in a document outline."""

    heading: str
    level: int = Field(ge=1, le=6, description="Heading level (1-6)")
    children: List["OutlineItem"] = Field(default_factory=list)
    query_hint: Optional[str] = Field(
        default=None, description="Optional hint to guide query generation"
    )

    def is_leaf(self) -> bool:
        """Check if this is a leaf node (no children).

        Returns:
            True if node has no children
        """
        return len(self.children) == 0

    def all_items(self) -> List["OutlineItem"]:
        """Get flattened list of all items including descendants.

        Returns:
            List of all outline items in tree order
        """
        items = [self]
        for child in self.children:
            items.extend(child.all_items())
        return items


class Outline(BaseModel):
    """Document outline with hierarchical structure."""

    title: str
    items: List[OutlineItem] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "Outline":
        """Load outline from YAML file.

        Expected YAML format:
        ```yaml
        title: "Chapter 3: Methodology"
        sections:
          - heading: "Introduction"
            level: 2
            subsections:
              - heading: "Background"
                level: 3
        ```

        Args:
            path: Path to YAML outline file

        Returns:
            Outline instance
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        def parse_section(section_data: dict) -> OutlineItem:
            """Recursively parse section and subsections."""
            item = OutlineItem(
                heading=section_data["heading"],
                level=section_data.get("level", 2),
                query_hint=section_data.get("query_hint"),
            )

            # Parse subsections recursively
            for subsection_data in section_data.get("subsections", []):
                item.children.append(parse_section(subsection_data))

            return item

        items = [parse_section(s) for s in data.get("sections", [])]

        return cls(title=data.get("title", "Untitled"), items=items)

    @classmethod
    def from_markdown(cls, path: Path) -> "Outline":
        """Load outline from Markdown file.

        Parses markdown headings to build hierarchy.

        Expected format:
        ```markdown
        # Chapter 3: Methodology

        ## Introduction
        ### Background
        ### Related Work

        ## Methods
        ```

        Args:
            path: Path to Markdown outline file

        Returns:
            Outline instance
        """
        with open(path) as f:
            content = f.read()

        lines = content.strip().split("\n")
        title = "Untitled"
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        # Parse headings with their levels
        headings: List[tuple[int, str]] = []

        for line in lines:
            match = heading_pattern.match(line.strip())
            if match:
                level = len(match.group(1))  # Count # symbols
                heading_text = match.group(2).strip()

                # First h1 becomes title
                if level == 1 and not headings:
                    title = heading_text
                else:
                    headings.append((level, heading_text))

        # Build tree structure
        if not headings:
            return cls(title=title, items=[])

        # Use a stack to build the tree
        root_items: List[OutlineItem] = []
        stack: List[tuple[int, OutlineItem]] = []

        for level, heading_text in headings:
            item = OutlineItem(heading=heading_text, level=level)

            # Pop stack until we find the parent level
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                # Add as child of top of stack
                stack[-1][1].children.append(item)
            else:
                # Top-level item
                root_items.append(item)

            # Push current item onto stack
            stack.append((level, item))

        return cls(title=title, items=root_items)


# Allow forward references for recursive model
OutlineItem.model_rebuild()

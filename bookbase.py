import streamlit as st
import json
import random
from pathlib import Path


# Data Persistence

def load_books():
    """Load books from JSON file. Returns empty list if file doesn't exist or is invalid."""
    books_file = Path('books.json')
    if books_file.exists():
        try:
            with open(books_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_books(books):
    """Save books to JSON file."""
    with open('books.json', 'w') as f:
        json.dump(books, f, indent=2)


def load_read_books():
    """Load reading history from JSON file."""
    read_file = Path('read_books.json')
    if read_file.exists():
        try:
            with open(read_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_read_books(read_books):
    """Save reading history to JSON file."""
    with open('read_books.json', 'w') as f:
        json.dump(read_books, f, indent=2)


# Helper Functions

def get_available_books(books, read_books):
    """Filter books to only include those ready to read, respecting series order."""
    available = []

    for book in books:
        if not book.get('series_name') or not book.get('series_number'):
            available.append(book)
            continue

        series_name = book['series_name']
        series_number = book['series_number']

        read_in_series = [
            b for b in read_books
            if b.get('series_name') == series_name
        ]

        if read_in_series:
            max_read = max(b.get('series_number', 0) for b in read_in_series)
            if series_number <= max_read + 1:
                available.append(book)
        else:
            if series_number == 1:
                available.append(book)

    return available


def show_book_edit_form(book, book_key):
    """Display the edit form for a book and handle save/cancel."""
    st.markdown("---")
    st.markdown("**Editing Book**")
    with st.form(key=f"edit_form_{book_key}"):
        edit_title = st.text_input("Title", value=book['title'])
        edit_author = st.text_input("Author", value=book['author'])
        edit_genre = st.text_input("Genre", value=book.get('genre', ''))
        edit_series = st.text_input("Series Name", value=book.get('series_name', ''))
        edit_number = st.number_input(
            "Series Order",
            min_value=1,
            value=book.get('series_number', 1),
            step=1
        )

        col1, col2 = st.columns(2)
        with col1:
            save_edit = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel_edit = st.form_submit_button("Cancel", use_container_width=True)

        if save_edit:
            book['title'] = edit_title
            book['author'] = edit_author
            book['genre'] = edit_genre if edit_genre else None
            book['series_name'] = edit_series if edit_series else None
            book['series_number'] = int(edit_number) if edit_series else None

            save_books(st.session_state.books)
            st.session_state[f'editing_{book_key}'] = False
            st.success("Book updated!")
            st.rerun()

        if cancel_edit:
            st.session_state[f'editing_{book_key}'] = False
            st.rerun()
    st.markdown("---")


# Main App

def main():
    st.set_page_config(
        page_title="My Reading List",
        layout="wide"
    )

    if 'books' not in st.session_state:
        st.session_state.books = load_books()
    if 'read_books' not in st.session_state:
        st.session_state.read_books = load_read_books()

    st.title("My Reading List")

    st.markdown("""
    Welcome! This app helps you manage your to-be-read (TBR) list and suggests what to read next
    while keeping track of series order.
    """)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Add Book",
        "My TBR List",
        "Get Suggestion",
        "Reading History"
    ])

    # TAB 1: Add Book
    with tab1:
        st.header("Add a New Book")
        st.info("Add books you want to read. Optional fields help with series tracking.")

        # Show modal confirmation if book was just added
        if st.session_state.get('show_add_confirmation'):
            @st.dialog("Book Added Successfully")
            def show_confirmation():
                st.success(st.session_state.book_added_message)
                if st.button("OK", type="primary", use_container_width=True):
                    st.session_state.show_add_confirmation = False
                    st.session_state.book_added_message = None
                    st.rerun()

            show_confirmation()

        with st.form("add_book_form", clear_on_submit=True):
            st.markdown("### Required Information")
            title = st.text_input(
                "Book Title *",
                help="Enter the full title of the book",
                placeholder="e.g., The Fellowship of the Ring"
            )
            author = st.text_input(
                "Author *",
                help="Enter the author's name",
                placeholder="e.g., J.R.R. Tolkien"
            )

            st.markdown("### Optional Information")
            st.caption("These fields are optional but help with organizing your list")

            genre = st.text_input(
                "Genre (optional)",
                help="e.g., Fantasy, Mystery, Romance",
                placeholder="e.g., Fantasy"
            )

            st.markdown("#### Series Information (optional)")
            st.caption(
                "If this book is part of a series, enter the details below. "
                "This helps ensure you read books in the correct order."
            )

            col1, col2 = st.columns(2)
            with col1:
                series_name = st.text_input(
                    "Series Name",
                    help="Name of the book series",
                    placeholder="e.g., The Lord of the Rings"
                )
            with col2:
                series_number = st.number_input(
                    "Series Order",
                    min_value=1,
                    value=1,
                    step=1,
                    help="Enter 1 for first book, 2 for second book, etc."
                )

            st.caption("⏱️ This will take just a few seconds to add to your list.")

            submitted = st.form_submit_button(
                "Add Book to TBR",
                type="primary",
                use_container_width=True
            )


            if submitted:
                if title and author:
                    new_book = {
                        'title': title,
                        'author': author,
                        'genre': genre if genre else None,
                        'series_name': series_name if series_name else None,
                        'series_number': int(series_number) if series_name else None
                    }

                    st.session_state.books.append(new_book)
                    save_books(st.session_state.books)

                    st.session_state.book_added_message = f"'{title}' has been added to your TBR list!"
                    st.session_state.show_add_confirmation = True
                    st.rerun()
                else:
                    st.error("Please fill in both Title and Author (marked with *)")

    # TAB 2: View TBR List
    with tab2:
        st.header("My TBR List")

        if not st.session_state.books:
            st.info("Your TBR list is empty. Add some books in the 'Add Book' tab!")
        else:
            st.success(f"You have {len(st.session_state.books)} book(s) in your TBR list")

            series_books = {}
            standalone_books = []

            for book in st.session_state.books:
                series_name = book.get('series_name')
                if series_name and series_name.strip():
                    series_key = series_name.strip()
                    if series_key not in series_books:
                        series_books[series_key] = []
                    series_books[series_key].append(book)
                else:
                    standalone_books.append(book)

            if series_books:
                st.subheader("Series Books")
                for series_name, books in sorted(series_books.items()):
                    books.sort(key=lambda x: x.get('series_number', 0))

                    with st.expander(f"**{series_name}** ({len(books)} book(s))", expanded=True):
                        for book in books:
                            book_key = f"{book['title']}_{book.get('series_number', 0)}"

                            if st.session_state.get(f'editing_{book_key}', False):
                                show_book_edit_form(book, book_key)
                            else:
                                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                                with col1:
                                    st.markdown(f"**Book {book['series_number']}: {book['title']}**")
                                    st.caption(f"by {book['author']}")
                                    if book.get('genre'):
                                        st.caption(f"Genre: {book['genre']}")
                                with col2:
                                    if st.button("Edit", key=f"edit_{book_key}", help="Edit book"):
                                        st.session_state[f'editing_{book_key}'] = True
                                        st.rerun()
                                with col3:
                                    if st.button("Mark Read", key=f"read_{book_key}", help="Mark as read"):
                                        st.session_state.books.remove(book)
                                        st.session_state.read_books.append(book)
                                        save_books(st.session_state.books)
                                        save_read_books(st.session_state.read_books)
                                        st.success(f"Marked '{book['title']}' as read!")
                                        st.rerun()
                                with col4:
                                    if st.button("Remove", key=f"remove_{book_key}", help="Remove from list"):
                                        st.session_state.books.remove(book)
                                        save_books(st.session_state.books)
                                        st.rerun()

            if standalone_books:
                st.subheader("Standalone Books")
                for book in standalone_books:
                    book_key = f"{book['title']}_standalone"

                    if st.session_state.get(f'editing_{book_key}', False):
                        show_book_edit_form(book, book_key)
                    else:
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        with col1:
                            st.markdown(f"**{book['title']}**")
                            st.caption(f"by {book['author']}")
                            if book.get('genre'):
                                st.caption(f"Genre: {book['genre']}")
                        with col2:
                            if st.button("Edit", key=f"edit_{book_key}", help="Edit book"):
                                st.session_state[f'editing_{book_key}'] = True
                                st.rerun()
                        with col3:
                            if st.button("Mark Read", key=f"read_{book_key}", help="Mark as read"):
                                st.session_state.books.remove(book)
                                st.session_state.read_books.append(book)
                                save_books(st.session_state.books)
                                save_read_books(st.session_state.read_books)
                                st.success(f"Marked '{book['title']}' as read!")
                                st.rerun()
                        with col4:
                            if st.button("Remove", key=f"remove_{book_key}", help="Remove from list"):
                                st.session_state.books.remove(book)
                                save_books(st.session_state.books)
                                st.rerun()

    # TAB 3: Get Suggestion
    with tab3:
        st.header("Get a Random Suggestion")

        st.markdown("""
        This will suggest a random book from your available titles (excluding series books you're not ready for).
        """)

        if not st.session_state.books:
            st.warning("Add some books to your TBR list first!")
        else:
            available_books = get_available_books(
                st.session_state.books,
                st.session_state.read_books
            )

            st.info(f"{len(available_books)} of {len(st.session_state.books)} books are available to suggest")

            if not available_books:
                st.warning("No books are currently available. You may need to read earlier books in your series first!")
            else:
                if st.button("Get Random Suggestion", type="primary", use_container_width=True):
                    if len(available_books) > 1 and st.session_state.get('last_suggestion'):
                        choices = [b for b in available_books if b != st.session_state.last_suggestion]
                        if choices:
                            available_books = choices

                    suggestion = random.choice(available_books)
                    st.session_state.last_suggestion = suggestion

                    st.success("### Your Next Read:")

                    with st.container():
                        st.markdown(f"## {suggestion['title']}")
                        st.markdown(f"### by {suggestion['author']}")

                        if suggestion.get('genre'):
                            st.caption(f"**Genre:** {suggestion['genre']}")

                        st.markdown("---")
                        st.markdown("**Why this book?**")
                        if suggestion.get('series_name'):
                            st.info(
                                f"This is book {suggestion['series_number']} "
                                f"in the {suggestion['series_name']} series"
                            )
                        else:
                            st.info("Standalone book - no series prerequisites!")

    # TAB 4: Reading History
    with tab4:
        st.header("Reading History")

        if not st.session_state.read_books:
            st.info("You haven't marked any books as read yet.")
        else:
            st.success(f"You've read {len(st.session_state.read_books)} book(s)!")

            for book in st.session_state.read_books:
                with st.expander(f"**{book['title']}** by {book['author']}"):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if book.get('genre'):
                            st.caption(f"Genre: {book['genre']}")
                        if book.get('series_name'):
                            st.caption(
                                f"Part of {book['series_name']} series "
                                f"(Book {book['series_number']})"
                            )
                    with col2:
                        if st.button("Unread",
                                     key=f"unread_{book['title']}_{book.get('series_number', 'standalone')}"):
                            st.session_state.read_books.remove(book)
                            st.session_state.books.append(book)
                            save_books(st.session_state.books)
                            save_read_books(st.session_state.read_books)
                            st.success(f"Moved '{book['title']}' back to TBR list!")
                            st.rerun()


if __name__ == "__main__":
    main()
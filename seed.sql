-- Categories
INSERT INTO categories (name, description, created_at, updated_at, is_deleted) VALUES
('Fiction', 'General fiction and literature', NOW(), NOW(), false),
('Fantasy', 'Magic and fantasy worlds', NOW(), NOW(), false),
('Mystery', 'Crime and detective stories', NOW(), NOW(), false),
('Horror', 'Horror and supernatural fiction', NOW(), NOW(), false),
('Literary Fiction', 'Serious, character-driven fiction', NOW(), NOW(), false);

-- Authors
INSERT INTO authors (name, biography, birth_date, nationality, created_at, updated_at, is_deleted) VALUES
('J.K. Rowling', 'British author best known for the Harry Potter series', '1965-07-31', 'British', NOW(), NOW(), false),
('George R.R. Martin', 'American novelist and short story writer', '1948-09-20', 'American', NOW(), NOW(), false),
('Haruki Murakami', 'Japanese writer and novelist', '1949-01-12', 'Japanese', NOW(), NOW(), false),
('Stephen King', 'American author of horror and fantasy', '1947-09-21', 'American', NOW(), NOW(), false),
('Agatha Christie', 'British mystery writer', '1890-09-15', 'British', NOW(), NOW(), false);

-- Users
INSERT INTO users (email, username, hashed_password, first_name, last_name, phone, address, role, face_embedding, created_at, updated_at, is_deleted) VALUES
('admin@library.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJyqJNme', 'Admin', 'User', '1234567890', '123 Admin St', 'ADMIN', NULL, NOW(), NOW(), false),
('member1@library.com', 'johndoe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJyqJNme', 'John', 'Doe', '0987654321', '456 Member Ave', 'MEMBER', NULL, NOW(), NOW(), false),
('member2@library.com', 'janesmith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJyqJNme', 'Jane', 'Smith', '5555555555', '789 Reader Rd', 'MEMBER', NULL, NOW(), NOW(), false);

-- Books
INSERT INTO books (title, isbn, author_id, publisher, publication_year, category_id, rent_fee, late_fee, total_copies, available_copies, created_at, updated_at, is_deleted) VALUES
('Harry Potter and the Philosopher''s Stone', '9780747532743', 1, 'Bloomsbury', 1997, 2, 5.00, 1.00, 10, 8, NOW(), NOW(), false),
('A Game of Thrones', '9780553103540', 2, 'Bantam Books', 1996, 2, 6.00, 1.00, 7, 5, NOW(), NOW(), false),
('Norwegian Wood', '9780375704024', 3, 'Vintage International', 1987, 5, 4.50, 1.00, 5, 3, NOW(), NOW(), false),
('The Shining', '9780385121675', 4, 'Doubleday', 1977, 4, 5.00, 1.00, 6, 4, NOW(), NOW(), false),
('Murder on the Orient Express', '9780062693662', 5, 'William Morrow', 1934, 3, 4.00, 1.00, 4, 2, NOW(), NOW(), false),
('1Q84', '9780307593313', 3, 'Knopf', 2011, 1, 6.00, 1.00, 3, 2, NOW(), NOW(), false),
('The Stand', '9780385121686', 4, 'Doubleday', 1978, 4, 5.50, 1.00, 5, 3, NOW(), NOW(), false);

-- Borrowing Books
INSERT INTO borrowing_books (user_id, book_id, borrow_date, due_date, return_date, status, created_at, updated_at, is_deleted) VALUES
(2, 1, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_ADD(NOW(), INTERVAL 20 DAY), NULL, 'BORROWED', NOW(), NOW(), false),
(3, 2, DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_ADD(NOW(), INTERVAL 15 DAY), NULL, 'BORROWED', NOW(), NOW(), false),
(2, 3, DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), 'RETURNED', NOW(), NOW(), false);

-- Borrowing Books (including overdue books)
INSERT INTO borrowing_books (user_id, book_id, borrow_date, due_date, return_date, status, created_at, updated_at, is_deleted) VALUES
(2, 1, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_ADD(NOW(), INTERVAL 20 DAY), NULL, 'BORROWED', NOW(), NOW(), false),
(3, 2, DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_ADD(NOW(), INTERVAL 15 DAY), NULL, 'BORROWED', NOW(), NOW(), false),
(2, 3, DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), 'RETURNED', NOW(), NOW(), false),

-- Overdue books
INSERT INTO borrowing_books (user_id, book_id, borrow_date, due_date, return_date, status, created_at, updated_at, is_deleted) VALUES
(2, 4, DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), NULL, 'OVERDUE', NOW(), NOW(), false),
(3, 5, DATE_SUB(NOW(), INTERVAL 45 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY), NULL, 'OVERDUE', NOW(), NOW(), false),
(2, 6, DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_SUB(NOW(), INTERVAL 30 DAY), NULL, 'OVERDUE', NOW(), NOW(), false),

-- Favorite Books
INSERT INTO favorite_books (user_id, book_id, created_at, updated_at, is_deleted) VALUES
(2, 1, NOW(), NOW(), false),
(2, 4, NOW(), NOW(), false),
(3, 2, NOW(), NOW(), false),
(3, 5, NOW(), NOW(), false);
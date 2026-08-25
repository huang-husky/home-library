import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { booksApi, type Book } from '@/api';
import { Search, Plus, BookOpen, Search as SearchIcon } from 'lucide-react';

function BookCard({ book }: { book: Book }) {
  const title = book.work?.title || book.edition?.title || '未知书名';
  const publisher = book.edition?.publisher;
  const isbn = book.edition?.isbn13;

  return (
    <Link
      to={`/books/${book.id}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4"
    >
      <div className="flex items-start space-x-4">
        <div className="w-16 h-20 bg-gray-200 rounded flex-shrink-0 flex items-center justify-center">
          {book.edition?.cover_url ? (
            <img
              src={book.edition.cover_url}
              alt={title}
              className="w-full h-full object-cover rounded"
            />
          ) : (
            <BookOpen className="w-8 h-8 text-gray-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{title}</h3>
          {publisher && (
            <p className="text-sm text-gray-500">{publisher}</p>
          )}
          {isbn && (
            <p className="text-xs text-gray-400 mt-1">ISBN: {isbn}</p>
          )}
          <div className="mt-2 flex items-center space-x-2">
            <span className={`px-2 py-0.5 text-xs rounded ${
              book.status === 'available'
                ? 'bg-green-100 text-green-800'
                : book.status === 'borrowed'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {book.status === 'available' ? '在库' : book.status === 'borrowed' ? '借出' : '丢失'}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

export function LibraryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const { data: booksData, isLoading } = useQuery({
    queryKey: ['books', 'list'],
    queryFn: () => booksApi.list({ limit: 50 }),
  });

  const { data: searchData, isLoading: isSearchLoading } = useQuery({
    queryKey: ['books', 'search', searchQuery],
    queryFn: () => booksApi.search(searchQuery),
    enabled: isSearching && searchQuery.length > 0,
  });

  const books = isSearching
    ? searchData?.data.items || []
    : booksData?.data.items || [];

  const total = isSearching
    ? searchData?.data.total || 0
    : booksData?.data.total || 0;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(searchQuery.length > 0);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">图书馆</h1>
          <p className="text-gray-600">共 {total} 本图书</p>
        </div>
        <div className="flex space-x-2">
          <Link
            to="/metadata/search"
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <SearchIcon className="w-4 h-4 mr-2" />
            搜索导入
          </Link>
          <Link
            to="/books/add"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            手动添加
          </Link>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex space-x-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="搜索书名、ISBN、出版社..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (e.target.value === '') setIsSearching(false);
            }}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          搜索
        </button>
      </form>

      {isLoading || isSearchLoading ? (
        <div className="text-center py-12">加载中...</div>
      ) : books.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow"
        >
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">{isSearching ? '没有找到匹配的图书' : '还没有图书，添加一本吧'}</p>
          {!isSearching && (
            <Link
              to="/books/add"
              className="text-blue-600 hover:text-blue-800 mt-2 inline-block"
            >
              添加图书 →
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </div>
  );
}

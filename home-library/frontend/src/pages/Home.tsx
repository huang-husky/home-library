import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { booksApi, bookshelvesApi } from '@/api';
import { BookOpen, Library, AlertCircle } from 'lucide-react';

export function HomePage() {
  const { data: booksData } = useQuery({
    queryKey: ['books', 'stats'],
    queryFn: () => booksApi.list({ limit: 1 }),
  });

  const { data: bookshelvesData } = useQuery({
    queryKey: ['bookshelves'],
    queryFn: () => bookshelvesApi.list(),
  });

  const totalBooks = booksData?.data.total || 0;
  const totalBookshelves = bookshelvesData?.data.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">HomeLib</h1>
          <p className="text-gray-600 mt-2">AI 家庭图书馆</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/bookshelves"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            书柜管理
          </Link>
          <Link
            to="/books/add"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            添加图书
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">总藏书</p>
              <p className="text-2xl font-semibold">{totalBooks}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <Library className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">书柜数量</p>
              <p className="text-2xl font-semibold">{totalBookshelves}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">待确认</p>
              <p className="text-2xl font-semibold">0</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">快速入口</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link
            to="/library"
            className="p-4 border rounded-lg hover:bg-gray-50 text-center"
          >
            <BookOpen className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>图书馆</p>
          </Link>
          <Link
            to="/bookshelves"
            className="p-4 border rounded-lg hover:bg-gray-50 text-center"
          >
            <Library className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>书柜管理</p>
          </Link>
        </div>
      </div>
    </div>
  );
}

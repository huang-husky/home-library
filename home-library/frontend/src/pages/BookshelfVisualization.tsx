import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { bookshelvesApi, shelfPositionApi } from '@/api';
import { MapPin, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export function BookshelfVisualizationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const shelfId = searchParams.get('shelf') ? Number(searchParams.get('shelf')) : null;
  const highlightBookId = searchParams.get('book') ? Number(searchParams.get('book')) : null;

  const [selectedShelfId, setSelectedShelfId] = useState<number | null>(shelfId);

  const { data: bookshelvesData } = useQuery({
    queryKey: ['bookshelves'],
    queryFn: () => bookshelvesApi.list(),
  });

  const { data: visualizationData, isLoading } = useQuery({
    queryKey: ['shelf-visualization', selectedShelfId],
    queryFn: () =>
      selectedShelfId ? shelfPositionApi.getShelfVisualization(selectedShelfId) : null,
    enabled: !!selectedShelfId,
  });

  const bookshelves = bookshelvesData?.data || [];
  const visualization = visualizationData?.data;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Link to="/library" className="text-gray-600 hover:text-gray-900 mr-3">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-2xl font-bold">书柜可视化</h1>
        </div>
      </div>

      {/* 书柜选择 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="font-semibold mb-3">选择书柜</h2>
        <div className="flex flex-wrap gap-2">
          {bookshelves.map((bookshelf: any) => (
            <button
              key={bookshelf.id}
              onClick={() => {
                setSelectedShelfId(bookshelf.id);
                setSearchParams({ shelf: bookshelf.id.toString() });
              }}
              className={`px-4 py-2 rounded-lg border ${
                selectedShelfId === bookshelf.id
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
              }`}
            >
              {bookshelf.name}
            </button>
          ))}
        </div>
      </div>

      {/* 书架可视化 */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-gray-500">加载中...</p>
        </div>
      )}

      {visualization && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {visualization.bookshelf_name} - 第 {visualization.level} 层
            </h2>
            <div className="text-sm text-gray-500">
              共 {visualization.books.length} 本书
            </div>
          </div>

          {/* 扫描原图 + 书籍位置 */}
          {visualization.scan_image_path ? (
            <div className="relative border rounded-lg overflow-hidden" style={{ minHeight: '300px' }}>
              <img
                src={`/api/scans/${visualization.latest_scan_id}/image`}
                alt="书架"
                className="w-full h-auto"
              />

              {/* 书籍标记 */}
              {visualization.books.map((book: any) => {
                const isHighlighted = book.book_id === highlightBookId;
                const bbox = book.bbox;

                if (!bbox) return null;

                return (
                  <Link
                    key={book.position_id}
                    to={`/books/${book.book_id}`}
                    className={`absolute border-2 transition-all hover:z-10 ${
                      isHighlighted
                        ? 'border-red-500 bg-red-500/30 z-20'
                        : 'border-blue-400 bg-blue-400/20 hover:bg-blue-400/40'
                    }`}
                    style={{
                      left: `${bbox.x * 100}%`,
                      top: `${bbox.y * 100}%`,
                      width: `${bbox.width * 100}%`,
                      height: `${bbox.height * 100}%`,
                    }}
                    title={`位置精度: ${Math.round(book.confidence * 100)}%`}
                  >
                    {isHighlighted && (
                      <div className="absolute -top-6 left-0 bg-red-500 text-white text-xs px-1 rounded whitespace-nowrap">
                        目标图书
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="bg-gray-100 rounded-lg p-8 text-center">
              <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">暂无扫描图片</p>
              <p className="text-sm text-gray-400 mt-1">
                请先前往扫描页面上传书架照片
              </p>
            </div>
          )}

          {/* 书籍列表 */}
          <div className="mt-6">
            <h3 className="font-semibold mb-3">书籍列表</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {visualization.books.map((book: any, index: number) => {
                const isHighlighted = book.book_id === highlightBookId;

                return (
                  <Link
                    key={book.position_id}
                    to={`/books/${book.book_id}`}
                    className={`p-3 border rounded-lg hover:shadow-md transition-shadow ${
                      isHighlighted ? 'border-red-500 bg-red-50' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">#{index + 1}</span>
                      <span className="text-sm text-gray-500">
                        精度: {Math.round(book.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      位置: {Math.round(book.position_x * 100)}%
                    </p>
                    {isHighlighted && (
                      <span className="inline-block mt-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded">
                        目标图书
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {!selectedShelfId && !isLoading && (
        <div className="text-center py-12 text-gray-500">
          <MapPin className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>请选择一个书柜查看可视化</p>
        </div>
      )}
    </div>
  );
}

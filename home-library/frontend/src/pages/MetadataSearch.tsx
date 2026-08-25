import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { metadataApi, bookImportApi, type BookMetadataCandidate } from '@/api';
import { Search, BookOpen, Loader2, ArrowLeft, Plus } from 'lucide-react';

interface CandidateCardProps {
  candidate: BookMetadataCandidate;
  onImport: (candidate: BookMetadataCandidate) => void;
}

function CandidateCard({ candidate, onImport }: CandidateCardProps) {
  const [isImporting, setIsImporting] = useState(false);

  const handleImport = async () => {
    setIsImporting(true);
    await onImport(candidate);
    setIsImporting(false);
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 flex gap-4">
      {/* 封面 */}
      <div className="w-24 h-36 flex-shrink-0 bg-gray-100 rounded overflow-hidden">
        {candidate.cover_url ? (
          <img
            src={candidate.cover_url}
            alt={candidate.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '';
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <BookOpen className="w-8 h-8" />
          </div>
        )}
      </div>

      {/* 信息 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-lg truncate">{candidate.title}</h3>
            {candidate.subtitle && (
              <p className="text-gray-500 text-sm truncate">{candidate.subtitle}</p>
            )}
          </div>
          <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-gray-600">
            {candidate.source === 'google_books' ? 'Google Books' : 'Open Library'}
          </span>
        </div>

        <div className="mt-2 space-y-1 text-sm">
          {candidate.authors.length > 0 && (
            <p className="text-gray-700">
              <span className="text-gray-500">作者:</span> {candidate.authors.join(', ')}
            </p>
          )}
          {candidate.publisher && (
            <p className="text-gray-700">
              <span className="text-gray-500">出版社:</span> {candidate.publisher}
            </p>
          )}
          {(candidate.publish_date || candidate.publish_year) && (
            <p className="text-gray-700">
              <span className="text-gray-500">出版时间:</span>{' '}
              {candidate.publish_date || candidate.publish_year}
            </p>
          )}
          {(candidate.isbn13 || candidate.isbn10) && (
            <p className="text-gray-700">
              <span className="text-gray-500">ISBN:</span>{' '}
              {candidate.isbn13 || candidate.isbn10}
            </p>
          )}
          {candidate.page_count && (
            <p className="text-gray-700">
              <span className="text-gray-500">页数:</span> {candidate.page_count}页
            </p>
          )}
        </div>

        {candidate.description && (
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">
            {candidate.description}
          </p>
        )}

        <div className="mt-4 flex gap-2">
          <button
            onClick={handleImport}
            disabled={isImporting}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isImporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Plus className="w-4 h-4 mr-2" />
            )}
            {isImporting ? '导入中...' : '导入'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function MetadataSearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [candidates, setCandidates] = useState<BookMetadataCandidate[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: bookImportApi.import,
    onSuccess: (response) => {
      if (response.data.success) {
        navigate(`/books/${response.data.book_id}`);
      }
    },
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    setError(null);

    try {
      const response = await metadataApi.search(query.trim(), 10);
      setCandidates(response.data.candidates);
    } catch (err) {
      setError('搜索失败，请稍后重试');
      setCandidates([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleImport = async (candidate: BookMetadataCandidate) => {
    await importMutation.mutateAsync({ candidate });
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Link to="/library" className="text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-2xl font-bold ml-3">搜索图书</h1>
        </div>
        <Link
          to="/books/add"
          className="inline-flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
        >
          <Plus className="w-4 h-4 mr-2" />
          手动录入
        </Link>
      </div>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入 ISBN 或书名搜索..."
              className="w-full px-4 py-3 pl-12 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isSearching ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              '搜索'
            )}
          </button>
        </div>
        <p className="mt-2 text-sm text-gray-500">
          支持 ISBN（10位或13位）或书名搜索，会从 Google Books 和 Open Library 获取数据
        </p>
      </form>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* 搜索结果 */}
      {hasSearched && (
        <div className="space-y-4">
          {isSearching ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
              <p className="mt-4 text-gray-500">正在搜索...</p>
            </div>
          ) : candidates.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">未找到相关图书</p>
              <Link
                to="/books/add"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                手动录入
              </Link>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500">
                找到 {candidates.length} 个结果
              </p>
              <div className="space-y-4">
                {candidates.map((candidate, index) => (
                  <CandidateCard
                    key={`${candidate.source}-${candidate.source_id}-${index}`}
                    candidate={candidate}
                    onImport={handleImport}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* 初始状态提示 */}
      {!hasSearched && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">输入 ISBN 或书名开始搜索</p>
        </div>
      )}
    </div>
  );
}

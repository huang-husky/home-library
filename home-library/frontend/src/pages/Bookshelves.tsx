import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bookshelvesApi, type Bookshelf } from '@/api';
import { Plus, Library, Trash2, ChevronDown, ChevronRight } from 'lucide-react';

function BookshelfCard({
  bookshelf,
  onDelete,
}: {
  bookshelf: Bookshelf;
  onDelete: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const { data: shelvesData } = useQuery({
    queryKey: ['shelves', bookshelf.id],
    queryFn: () => bookshelvesApi.listShelves(bookshelf.id),
    enabled: expanded,
  });

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {expanded ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </button>
          <div className="ml-2">
            <h3 className="font-semibold">{bookshelf.name}</h3>
            {bookshelf.location && (
              <p className="text-sm text-gray-500">位置: {bookshelf.location}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {bookshelf.shelf_count || 0} 层
          </span>
          <button
            onClick={() => onDelete(bookshelf.id)}
            className="p-2 text-red-600 hover:bg-red-50 rounded"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {expanded && shelvesData?.data && (
        <div className="mt-4 ml-6 space-y-2">
          {shelvesData.data.map((shelf) => (
            <div
              key={shelf.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded"
            >
              <span>第 {shelf.level} 层</span>
              <span className="text-sm text-gray-500">
                {shelf.book_count || 0} 本书
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function BookshelvesPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBookshelf, setNewBookshelf] = useState({
    name: '',
    location: '',
    description: '',
  });

  const queryClient = useQueryClient();

  const { data: bookshelvesData, isLoading } = useQuery({
    queryKey: ['bookshelves'],
    queryFn: () => bookshelvesApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: bookshelvesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookshelves'] });
      setShowAddModal(false);
      setNewBookshelf({ name: '', location: '', description: '' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: bookshelvesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookshelves'] });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBookshelf.name.trim()) return;
    createMutation.mutate(newBookshelf);
  };

  const handleDelete = (id: number) => {
    if (confirm('确定要删除这个书柜吗？')) {
      deleteMutation.mutate(id);
    }
  };

  const bookshelves = bookshelvesData?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">书柜管理</h1>
          <p className="text-gray-600">管理您的书柜和书架层</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          添加书柜
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">加载中...</div>
      ) : bookshelves.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <Library className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">还没有书柜，添加一个吧</p>
        </div>
      ) : (
        <div className="space-y-4">
          {bookshelves.map((bookshelf) => (
            <BookshelfCard
              key={bookshelf.id}
              bookshelf={bookshelf}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">添加书柜</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  名称 *
                </label>
                <input
                  type="text"
                  value={newBookshelf.name}
                  onChange={(e) =>
                    setNewBookshelf({ ...newBookshelf, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="如：客厅书柜"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  位置
                </label>
                <input
                  type="text"
                  value={newBookshelf.location}
                  onChange={(e) =>
                    setNewBookshelf({ ...newBookshelf, location: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="如：客厅"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={newBookshelf.description}
                  onChange={(e) =>
                    setNewBookshelf({ ...newBookshelf, description: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

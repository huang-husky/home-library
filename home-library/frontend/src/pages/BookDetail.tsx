import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { booksApi, shelfPositionApi } from '@/api';
import { ArrowLeft, Trash2, Edit, MapPin } from 'lucide-react';
import { useState } from 'react';

export function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    status: '',
    owner: '',
    notes: '',
  });

  const { data: bookData, isLoading } = useQuery({
    queryKey: ['book', id],
    queryFn: () => booksApi.get(Number(id)),
    enabled: !!id,
  });

  const { data: positionsData } = useQuery({
    queryKey: ['book-positions', id],
    queryFn: () => shelfPositionApi.getBookPositions(Number(id)),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { status?: string; owner?: string; notes?: string }) =>
      booksApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['book', id] });
      queryClient.invalidateQueries({ queryKey: ['books'] });
      setIsEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => booksApi.delete(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
      navigate('/library');
    },
  });

  if (isLoading) return <div className="text-center py-12">加载中...</div>;
  if (!bookData?.data) return <div className="text-center py-12">图书不存在</div>;

  const book = bookData.data;
  const title = book.work?.title || book.edition?.title || '未知书名';
  const subtitle = book.work?.subtitle;

  // 获取当前位置
  const positions = positionsData?.data || [];
  const currentPosition = positions.find(p => p.is_current);

  const handleUpdate = () => {
    updateMutation.mutate(editForm);
  };

  const handleDelete = () => {
    if (confirm('确定要删除这本书吗？')) {
      deleteMutation.mutate();
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Link to="/library" className="text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-2xl font-bold ml-3">图书详情</h1>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => {
              setEditForm({
                status: book.status,
                owner: book.owner || '',
                notes: book.notes || '',
              });
              setIsEditing(true);
            }}
            className="flex items-center px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <Edit className="w-4 h-4 mr-1" />
            编辑
          </button>
          <button
            onClick={handleDelete}
            className="flex items-center px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            删除
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <h2 className="text-2xl font-bold">{title}</h2>
          {subtitle && <p className="text-gray-600">{subtitle}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">ISBN</p>
            <p>{book.edition?.isbn13 || '-'}</p>
          </div>
          <div>
            <p className="text-gray-500">出版社</p>
            <p>{book.edition?.publisher || '-'}</p>
          </div>
          <div>
            <p className="text-gray-500">状态</p>
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
          <div>
            <p className="text-gray-500">所有者</p>
            <p>{book.owner || '-'}</p>
          </div>
        </div>

        {book.notes && (
          <div>
            <p className="text-gray-500 text-sm">备注</p>
            <p className="mt-1">{book.notes}</p>
          </div>
        )}

        {/* 位置信息 */}
        <div className="border-t pt-4 mt-4">
          <h3 className="font-semibold mb-3 flex items-center">
            <MapPin className="w-4 h-4 mr-1" />
            位置信息
          </h3>

          {currentPosition ? (
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">书柜信息</p>
                  <p className="text-sm text-gray-600">
                    书架 ID: {currentPosition.shelf_id}
                  </p>
                  {currentPosition.position_order && (
                    <p className="text-sm text-gray-600">
                      左起约第 {currentPosition.position_order} 本
                    </p>
                  )}
                  <p className="text-sm text-gray-500 mt-1">
                    位置精度: {Math.round(currentPosition.confidence * 100)}%
                  </p>
                </div>
                <Link
                  to={`/bookshelf-visualization?shelf=${currentPosition.shelf_id}`}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  查看书柜位置
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">
              暂无位置信息
              {positions.length > 0 && ` (有 ${positions.length} 条历史位置记录)`}
            </div>
          )}
        </div>

        <div className="text-xs text-gray-400 pt-4 border-t">
          <p>创建时间: {new Date(book.created_at).toLocaleString()}</p>
          <p>更新时间: {new Date(book.updated_at).toLocaleString()}</p>
        </div>
      </div>

      {isEditing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑图书</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="available">在库</option>
                  <option value="borrowed">借出</option>
                  <option value="lost">丢失</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">所有者</label>
                <input
                  type="text"
                  value={editForm.owner}
                  onChange={(e) => setEditForm({ ...editForm, owner: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={handleUpdate}
                disabled={updateMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {updateMutation.isPending ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

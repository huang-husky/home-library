import React, { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Image as ImageIcon, Check, X, Trash2, Plus, AlertCircle, BarChart3 } from 'lucide-react';
import { scansApi, bookshelvesApi, ScanItem, BoundingBox } from '../api';

interface SelectedBox {
  item: ScanItem;
  isEditing: boolean;
  editText: string;
}

export default function ShelfScan() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);

  // 选择状态
  const [selectedBookshelfId, setSelectedBookshelfId] = useState<number | ''>('');
  const [selectedShelfId, setSelectedShelfId] = useState<number | ''>('');

  // 扫描状态
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [currentScanId, setCurrentScanId] = useState<number | null>(null);
  const [scanItems, setScanItems] = useState<ScanItem[]>([]);
  const [selectedBox, setSelectedBox] = useState<SelectedBox | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const [drawCurrent, setDrawCurrent] = useState<{ x: number; y: number } | null>(null);
  const [newBoxText, setNewBoxText] = useState('');

  // 获取书柜列表
  const { data: bookshelves = [] } = useQuery({
    queryKey: ['bookshelves'],
    queryFn: () => bookshelvesApi.list().then(r => r.data),
  });

  // 获取层列表
  const { data: shelves = [] } = useQuery({
    queryKey: ['shelves', selectedBookshelfId],
    queryFn: () => selectedBookshelfId ? bookshelvesApi.listShelves(selectedBookshelfId).then(r => r.data) : Promise.resolve([]),
    enabled: !!selectedBookshelfId,
  });

  // 上传并识别
  const uploadMutation = useMutation({
    mutationFn: (file: File) => scansApi.upload(
      file,
      selectedBookshelfId || undefined,
      selectedShelfId || undefined
    ),
    onSuccess: (response) => {
      setCurrentScanId(response.data.scan_id);
      setScanItems(response.data.items);
      // 刷新扫描列表
      queryClient.invalidateQueries({ queryKey: ['scans'] });
    },
  });

  // 更新扫描项
  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: Partial<ScanItem> }) =>
      scansApi.updateItem(itemId, data),
    onSuccess: () => {
      if (currentScanId) {
        scansApi.getItems(currentScanId).then(r => setScanItems(r.data));
      }
    },
  });

  // 删除扫描项
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => scansApi.deleteItem(itemId),
    onSuccess: () => {
      if (currentScanId) {
        scansApi.getItems(currentScanId).then(r => setScanItems(r.data));
      }
      setSelectedBox(null);
    },
  });

  // 添加扫描项
  const addItemMutation = useMutation({
    mutationFn: (data: { text: string; bbox: BoundingBox }) =>
      scansApi.addItem(currentScanId!, data),
    onSuccess: () => {
      if (currentScanId) {
        scansApi.getItems(currentScanId).then(r => setScanItems(r.data));
      }
      setNewBoxText('');
      setIsDrawing(false);
      setDrawStart(null);
      setDrawCurrent(null);
    },
  });

  // 文件选择处理
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 预览图片
    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target?.result as string);
    };
    reader.readAsDataURL(file);

    // 上传并识别
    uploadMutation.mutate(file);
  };

  // 获取置信度颜色
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'text-green-600';
      case 'rejected': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  // 处理图片点击开始绘制新框
  const handleImageMouseDown = (e: React.MouseEvent) => {
    if (!uploadedImage) return;
    const rect = imageContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    setIsDrawing(true);
    setDrawStart({ x, y });
    setDrawCurrent({ x, y });
  };

  const handleImageMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !drawStart) return;
    const rect = imageContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setDrawCurrent({ x, y });
  };

  const handleImageMouseUp = () => {
    if (!isDrawing || !drawStart || !drawCurrent) return;

    const width = Math.abs(drawCurrent.x - drawStart.x);
    const height = Math.abs(drawCurrent.y - drawStart.y);

    if (width > 0.02 && height > 0.05) {
      // 框足够大，可以添加
      const x = Math.min(drawStart.x, drawCurrent.x);
      const y = Math.min(drawStart.y, drawCurrent.y);
      setDrawStart({ x, y });
    }

    setIsDrawing(false);
  };

  // 完成手动添加
  const handleAddNewBox = () => {
    if (!drawStart || !drawCurrent || !newBoxText.trim()) return;

    const x = Math.min(drawStart.x, drawCurrent.x);
    const y = Math.min(drawStart.y, drawCurrent.y);
    const width = Math.abs(drawCurrent.x - drawStart.x);
    const height = Math.abs(drawCurrent.y - drawCurrent.y);

    addItemMutation.mutate({
      text: newBoxText,
      bbox: { x, y, width, height },
    });
  };

  // 统计
  const stats = {
    total: scanItems.length,
    high: scanItems.filter(i => i.confidence >= 0.8).length,
    medium: scanItems.filter(i => i.confidence >= 0.5 && i.confidence < 0.8).length,
    low: scanItems.filter(i => i.confidence < 0.5).length,
    detected: scanItems.filter(i => i.status === 'detected').length,
    confirmed: scanItems.filter(i => i.status === 'confirmed').length,
    failed: scanItems.filter(i => i.status === 'failed').length,
    skipped: scanItems.filter(i => i.status === 'skipped').length,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">书架扫描</h1>

      {/* 选择区域 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 书柜选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择书柜
            </label>
            <select
              value={selectedBookshelfId}
              onChange={(e) => {
                setSelectedBookshelfId(e.target.value ? Number(e.target.value) : '');
                setSelectedShelfId('');
              }}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择书柜</option>
              {bookshelves.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>

          {/* 层选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择层
            </label>
            <select
              value={selectedShelfId}
              onChange={(e) => setSelectedShelfId(e.target.value ? Number(e.target.value) : '')}
              disabled={!selectedBookshelfId}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            >
              <option value="">请选择层</option>
              {shelves.map(s => (
                <option key={s.id} value={s.id}>第 {s.level} 层</option>
              ))}
            </select>
          </div>

          {/* 上传按钮 */}
          <div className="flex items-end">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  识别中...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  上传书架照片
                </>
              )}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {uploadedImage && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 图片预览区 */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <ImageIcon className="w-5 h-5" />
                识别结果预览
              </h2>
              <div className="text-sm text-gray-500">
                {scanItems.length} 本书被识别
              </div>
            </div>

            {/* 统计条 */}
            <div className="flex gap-2 mb-4 text-xs">
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                高置信度: {stats.high}
              </span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">
                中置信度: {stats.medium}
              </span>
              <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                低置信度: {stats.low}
              </span>
            </div>

            {/* 图片容器 */}
            <div
              ref={imageContainerRef}
              className="relative border rounded overflow-hidden select-none"
              onMouseDown={handleImageMouseDown}
              onMouseMove={handleImageMouseMove}
              onMouseUp={handleImageMouseUp}
              onMouseLeave={handleImageMouseUp}
            >
              <img
                src={uploadedImage}
                alt="书架"
                className="w-full h-auto"
                draggable={false}
              />

              {/* 渲染所有识别框 */}
              {scanItems.map((item) => (
                item.bbox && (
                  <div
                    key={item.id}
                    className={`absolute border-2 cursor-pointer transition-all ${
                      selectedBox?.item.id === item.id
                        ? 'border-blue-500 bg-blue-500/20'
                        : item.status === 'rejected'
                        ? 'border-red-400 bg-red-400/10'
                        : item.status === 'confirmed'
                        ? 'border-green-400 bg-green-400/10'
                        : `border-opacity-50 bg-opacity-10 ${getConfidenceColor(item.confidence)}`
                    }`}
                    style={{
                      left: `${item.bbox.x * 100}%`,
                      top: `${item.bbox.y * 100}%`,
                      width: `${item.bbox.width * 100}%`,
                      height: `${item.bbox.height * 100}%`,
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedBox({
                        item,
                        isEditing: false,
                        editText: item.detected_text,
                      });
                    }}
                    title={`${item.detected_text} (${Math.round(item.confidence * 100)}%)`}
                  >
                    {/* 标签 */}
                    <div className={`absolute -top-5 left-0 text-xs px-1 rounded whitespace-nowrap ${getConfidenceColor(item.confidence)} text-white`}>
                      {item.detected_text.slice(0, 10)}{item.detected_text.length > 10 ? '...' : ''}
                    </div>
                  </div>
                )
              ))}

              {/* 正在绘制的新框 */}
              {isDrawing && drawStart && drawCurrent && (
                <div
                  className="absolute border-2 border-dashed border-blue-500 bg-blue-500/20"
                  style={{
                    left: `${Math.min(drawStart.x, drawCurrent.x) * 100}%`,
                    top: `${Math.min(drawStart.y, drawCurrent.y) * 100}%`,
                    width: `${Math.abs(drawCurrent.x - drawStart.x) * 100}%`,
                    height: `${Math.abs(drawCurrent.y - drawStart.y) * 100}%`,
                  }}
                />
              )}
            </div>

            <p className="text-sm text-gray-500 mt-2">
              点击图片上的框可以编辑，拖拽鼠标可添加新框
            </p>
          </div>

          {/* 识别项列表 */}
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              识别详情
            </h2>

            {/* 添加新框表单 */}
            {drawStart && drawCurrent && !isDrawing && (
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <h3 className="font-medium mb-2">添加新识别项</h3>
                <input
                  type="text"
                  value={newBoxText}
                  onChange={(e) => setNewBoxText(e.target.value)}
                  placeholder="输入书名"
                  className="w-full px-3 py-2 border rounded mb-2"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddNewBox}
                    disabled={!newBoxText.trim() || addItemMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    <Plus className="w-4 h-4 inline mr-1" />
                    添加
                  </button>
                  <button
                    onClick={() => {
                      setDrawStart(null);
                      setDrawCurrent(null);
                      setNewBoxText('');
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}

            {/* 选中的项详情 */}
            {selectedBox && (
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">编辑识别项</h3>
                  <button
                    onClick={() => setSelectedBox(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {selectedBox.isEditing ? (
                  <input
                    type="text"
                    value={selectedBox.editText}
                    onChange={(e) => setSelectedBox({ ...selectedBox, editText: e.target.value })}
                    className="w-full px-3 py-2 border rounded mb-2"
                  />
                ) : (
                  <p className="text-lg mb-2">{selectedBox.item.detected_text}</p>
                )}

                <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                  <span>置信度: {Math.round(selectedBox.item.confidence * 100)}%</span>
                  <span className={getStatusColor(selectedBox.item.status)}>
                    状态: {selectedBox.item.status === 'detected' ? '待确认' : selectedBox.item.status === 'confirmed' ? '已确认' : selectedBox.item.status === 'failed' ? '失败' : selectedBox.item.status === 'skipped' ? '已跳过' : '待处理'}
                  </span>
                </div>

                <div className="flex gap-2 flex-wrap">
                  {selectedBox.isEditing ? (
                    <>
                      <button
                        onClick={() => {
                          updateItemMutation.mutate({
                            itemId: selectedBox.item.id,
                            data: { detected_text: selectedBox.editText },
                          });
                          setSelectedBox(null);
                        }}
                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
                      >
                        <Check className="w-4 h-4 inline mr-1" />
                        保存
                      </button>
                      <button
                        onClick={() => setSelectedBox({ ...selectedBox, isEditing: false, editText: selectedBox.item.detected_text })}
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm"
                      >
                        取消
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => setSelectedBox({ ...selectedBox, isEditing: true })}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => updateItemMutation.mutate({
                          itemId: selectedBox.item.id,
                          data: { status: 'confirmed' },
                        })}
                        className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm"
                      >
                        <Check className="w-4 h-4 inline mr-1" />
                        确认
                      </button>
                      <button
                        onClick={() => updateItemMutation.mutate({
                          itemId: selectedBox.item.id,
                          data: { status: 'rejected' },
                        })}
                        className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded text-sm"
                      >
                        <AlertCircle className="w-4 h-4 inline mr-1" />
                        拒绝
                      </button>
                      <button
                        onClick={() => deleteItemMutation.mutate(selectedBox.item.id)}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm"
                      >
                        <Trash2 className="w-4 h-4 inline mr-1" />
                        删除
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* 识别项列表 */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {scanItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedBox({ item, isEditing: false, editText: item.detected_text })}
                  className={`p-3 border rounded cursor-pointer transition-all ${
                    selectedBox?.item.id === item.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${item.status === 'rejected' ? 'opacity-50' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-medium ${item.detected_text.startsWith('[') ? 'text-gray-400' : ''}`}>
                      {item.detected_text}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded text-white ${getConfidenceColor(item.confidence)}`}>
                        {Math.round(item.confidence * 100)}%
                      </span>
                      {item.status === 'confirmed' && <Check className="w-4 h-4 text-green-600" />}
                      {item.status === 'rejected' && <X className="w-4 h-4 text-red-600" />}
                    </div>
                  </div>
                </div>
              ))}

              {scanItems.length === 0 && !uploadMutation.isPending && (
                <div className="text-center text-gray-500 py-8">
                  暂无识别结果
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 提示信息 */}
      {!uploadedImage && !uploadMutation.isPending && (
        <div className="text-center py-16 text-gray-500">
          <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>选择书柜和层，然后上传书架照片开始识别</p>
          <p className="text-sm mt-2">支持 JPG、PNG 格式</p>
        </div>
      )}
    </div>
  );
}

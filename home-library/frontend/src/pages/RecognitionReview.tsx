import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  Check, X, RefreshCw, SkipForward, BookOpen, AlertCircle,
  ChevronLeft, ChevronRight, Library, BarChart3, Play,
  ThumbsUp, ThumbsDown, RotateCcw
} from 'lucide-react';
import { scansApi, aiImportApi, ImportItem, ImportCandidate } from '../api';

export default function RecognitionReview() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const scanId = parseInt(searchParams.get('scan') || '0');

  // UI 状态
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const [currentCandidateIndex, setCurrentCandidateIndex] = useState(0);
  const [actionLog, setActionLog] = useState<string[]>([]);
  const imageContainerRef = useRef<HTMLDivElement>(null);

  // 获取扫描列表
  const { data: scans = [] } = useQuery({
    queryKey: ['scans'],
    queryFn: () => scansApi.list().then(r => r.data),
  });

  // 获取导入项
  const { data: importData, isLoading } = useQuery({
    queryKey: ['import-items', scanId],
    queryFn: () => scanId ? aiImportApi.getItems(scanId).then(r => r.data) : Promise.resolve(null),
    enabled: !!scanId,
  });

  // 选中的项目
  const selectedItem = importData?.items.find(i => i.id === selectedItemId) ||
                       importData?.items[0];

  // 执行匹配
  const matchMutation = useMutation({
    mutationFn: (id: number) => aiImportApi.match(id),
    onSuccess: (result) => {
      addLog(`匹配完成: ${result.data.summary.confirmed} 个自动确认, ${result.data.summary.needs_review} 个需审核`);
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 选择候选
  const selectMutation = useMutation({
    mutationFn: ({ itemId, index }: { itemId: number; index: number }) =>
      aiImportApi.selectCandidate(itemId, index),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 跳过项目
  const skipMutation = useMutation({
    mutationFn: (itemId: number) => aiImportApi.skip(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 导入项目
  const importMutation = useMutation({
    mutationFn: (itemId: number) => aiImportApi.import(itemId),
    onSuccess: (result) => {
      addLog(`成功导入: 书籍 ID ${result.data.book_id}`);
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 批量导入
  const batchImportMutation = useMutation({
    mutationFn: () => scanId ? aiImportApi.batchImport(scanId) : Promise.reject('No scan'),
    onSuccess: (result) => {
      addLog(`批量导入完成: ${result.data.imported} 成功, ${result.data.failed} 失败`);
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 自动确认
  const autoConfirmMutation = useMutation({
    mutationFn: () => scanId ? aiImportApi.autoConfirm(scanId) : Promise.reject('No scan'),
    onSuccess: (result) => {
      addLog(`自动确认: ${result.data.confirmed_count} 个项目`);
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  // 重新匹配
  const retryMutation = useMutation({
    mutationFn: (itemId: number) => aiImportApi.retry(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-items', scanId] });
    },
  });

  const addLog = (message: string) => {
    setActionLog(prev => [`[${new Date().toLocaleTimeString()}] ${message}`, ...prev].slice(0, 20));
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'imported': return 'bg-green-500 text-white';
      case 'confirmed': return 'bg-blue-500 text-white';
      case 'matched': return 'bg-cyan-400 text-white';
      case 'needs_review': return 'bg-yellow-400 text-black';
      case 'failed': return 'bg-red-500 text-white';
      case 'skipped': return 'bg-gray-400 text-white';
      default: return 'bg-gray-200 text-gray-700';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      detected: '已检测',
      searching: '搜索中',
      matched: '已匹配',
      needs_review: '需审核',
      confirmed: '已确认',
      imported: '已导入',
      failed: '失败',
      skipped: '已跳过',
    };
    return labels[status] || status;
  };

  const stats = importData?.stats;

  if (!scanId) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">识别审核与导入</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">选择扫描记录</h2>
          {scans.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无扫描记录，请先前往扫描页面上传图片</p>
            </div>
          ) : (
            <div className="space-y-2">
              {scans.map(scan => (
                <div
                  key={scan.id}
                  onClick={() => setSearchParams({ scan: scan.id.toString() })}
                  className="p-4 border rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all flex items-center justify-between"
                >
                  <div>
                    <span className="font-medium">扫描 #{scan.id}</span>
                    <p className="text-sm text-gray-500">
                      {new Date(scan.scanned_at).toLocaleString()} · {scan.item_count} 本书
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">识别审核与导入</h1>
        <button
          onClick={() => setSearchParams({})}
          className="px-4 py-2 text-gray-600 hover:text-gray-800"
        >
          返回列表
        </button>
      </div>

      {/* 统计栏 */}
      {stats && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              扫描统计
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => matchMutation.mutate(scanId)}
                disabled={matchMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2"
              >
                {matchMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                执行匹配
              </button>
              <button
                onClick={() => autoConfirmMutation.mutate()}
                disabled={autoConfirmMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
              >
                <ThumbsUp className="w-4 h-4" />
                自动确认高置信度
              </button>
              <button
                onClick={() => batchImportMutation.mutate()}
                disabled={batchImportMutation.isPending}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 flex items-center gap-2"
              >
                <Library className="w-4 h-4" />
                批量导入
              </button>
            </div>
          </div>

          <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-gray-500">总计</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded">
              <div className="text-2xl font-bold text-blue-600">{stats.confirmed}</div>
              <div className="text-xs text-gray-500">已确认</div>
            </div>
            <div className="text-center p-3 bg-cyan-50 rounded">
              <div className="text-2xl font-bold text-cyan-600">{stats.matched}</div>
              <div className="text-xs text-gray-500">已匹配</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded">
              <div className="text-2xl font-bold text-yellow-600">{stats.needs_review}</div>
              <div className="text-xs text-gray-500">需审核</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded">
              <div className="text-2xl font-bold text-green-600">{stats.imported}</div>
              <div className="text-xs text-gray-500">已导入</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-gray-600">{stats.detected}</div>
              <div className="text-xs text-gray-500">待匹配</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded">
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
              <div className="text-xs text-gray-500">失败</div>
            </div>
            <div className="text-center p-3 bg-gray-100 rounded">
              <div className="text-2xl font-bold text-gray-600">{stats.skipped}</div>
              <div className="text-xs text-gray-500">已跳过</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：项目列表 */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">识别项目</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {importData?.items.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  setSelectedItemId(item.id);
                  setCurrentCandidateIndex(0);
                }}
                className={`p-3 border rounded cursor-pointer transition-all ${
                  selectedItem?.id === item.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium truncate">{item.detected_text}</span>
                  <span className={`text-xs px-2 py-1 rounded ${getStatusColor(item.status)}`}>
                    {getStatusLabel(item.status)}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
                  <span>置信度: {Math.round(item.confidence * 100)}%</span>
                  <span>候选: {item.candidates_count}</span>
                </div>
              </div>
            ))}
            {importData?.items.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                暂无识别项目
              </div>
            )}
          </div>
        </div>

        {/* 中间：图片预览 */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">原图预览</h3>
          {importData?.image_path ? (
            <div
              ref={imageContainerRef}
              className="relative border rounded overflow-hidden"
            >
              <img
                src={`/api/scans/${scanId}/image`}
                alt="书架"
                className="w-full h-auto"
                onError={(e) => {
                  // 如果图片加载失败，显示占位符
                  e.currentTarget.style.display = 'none';
                }}
              />
              {/* 渲染 bbox */}
              {selectedItem?.bbox && (
                <div
                  className="absolute border-2 border-blue-500 bg-blue-500/20"
                  style={{
                    left: `${selectedItem.bbox.x * 100}%`,
                    top: `${selectedItem.bbox.y * 100}%`,
                    width: `${selectedItem.bbox.width * 100}%`,
                    height: `${selectedItem.bbox.height * 100}%`,
                  }}
                >
                  <div className="absolute -top-5 left-0 bg-blue-500 text-white text-xs px-1 rounded">
                    {selectedItem.detected_text.slice(0, 15)}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="aspect-video bg-gray-100 rounded flex items-center justify-center">
              <span className="text-gray-400">图片加载中...</span>
            </div>
          )}

          {/* 操作日志 */}
          {actionLog.length > 0 && (
            <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
              <h4 className="font-medium mb-2">操作日志</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {actionLog.map((log, i) => (
                  <div key={i} className="text-gray-600">{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 右侧：审核详情 */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-4">审核详情</h3>

          {selectedItem ? (
            <div>
              {/* 检测文本 */}
              <div className="mb-4 p-3 bg-gray-50 rounded">
                <label className="text-xs text-gray-500">检测文本</label>
                <div className="text-lg font-medium">{selectedItem.detected_text}</div>
                <div className="text-sm text-gray-500 mt-1">
                  置信度: {Math.round(selectedItem.confidence * 100)}%
                </div>
              </div>

              {/* 候选列表 */}
              {selectedItem.candidates && selectedItem.candidates.length > 0 ? (
                <div className="mb-4">
                  <label className="text-xs text-gray-500">候选图书 ({selectedItem.candidates.length})</label>

                  {/* 候选导航 */}
                  <div className="flex items-center justify-between my-2">
                    <button
                      onClick={() => setCurrentCandidateIndex(Math.max(0, currentCandidateIndex - 1))}
                      disabled={currentCandidateIndex === 0}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="text-sm text-gray-600">
                      {currentCandidateIndex + 1} / {selectedItem.candidates.length}
                    </span>
                    <button
                      onClick={() => setCurrentCandidateIndex(Math.min(selectedItem.candidates.length - 1, currentCandidateIndex + 1))}
                      disabled={currentCandidateIndex >= selectedItem.candidates.length - 1}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>

                  {/* 候选详情 */}
                  {(() => {
                    const candidate = selectedItem.candidates[currentCandidateIndex];
                    const isSelected = selectedItem.matched_candidate_index === currentCandidateIndex;
                    return (
                      <div className={`p-3 border rounded ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                        {candidate.cover_url && (
                          <img
                            src={candidate.cover_url}
                            alt={candidate.title}
                            className="w-24 h-32 object-cover rounded mx-auto mb-2"
                          />
                        )}
                        <div className="font-medium text-center">{candidate.title}</div>
                        {candidate.subtitle && (
                          <div className="text-sm text-gray-500 text-center">{candidate.subtitle}</div>
                        )}
                        <div className="text-sm text-gray-600 text-center mt-1">
                          {candidate.authors?.join(', ')}
                        </div>
                        <div className="text-xs text-gray-400 text-center mt-1">
                          {candidate.publisher} {candidate.publish_year && `· ${candidate.publish_year}`}
                        </div>
                        {candidate.isbn13 && (
                          <div className="text-xs text-gray-400 text-center">
                            ISBN: {candidate.isbn13}
                          </div>
                        )}

                        {isSelected && selectedItem.match_confidence && (
                          <div className="mt-2 text-center">
                            <span className={`text-sm px-2 py-1 rounded ${
                              selectedItem.match_confidence >= 0.8 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              匹配置信度: {Math.round(selectedItem.match_confidence * 100)}%
                            </span>
                          </div>
                        )}

                        {/* 选择此候选 */}
                        {!isSelected && (
                          <button
                            onClick={() => selectMutation.mutate({ itemId: selectedItem.id, index: currentCandidateIndex })}
                            disabled={selectMutation.isPending}
                            className="w-full mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            选择此版本
                          </button>
                        )}
                      </div>
                    );
                  })()}
                </div>
              ) : selectedItem.status === 'failed' ? (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded">
                  <AlertCircle className="w-5 h-5 inline mr-2" />
                  {selectedItem.search_error || '搜索失败'}
                </div>
              ) : selectedItem.status === 'searching' ? (
                <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded">
                  <RefreshCw className="w-5 h-5 inline mr-2 animate-spin" />
                  搜索中...
                </div>
              ) : (
                <div className="mb-4 p-3 bg-gray-50 text-gray-500 rounded">
                  暂无候选，请先执行匹配
                </div>
              )}

              {/* 操作按钮 */}
              <div className="space-y-2">
                {selectedItem.status === 'confirmed' && (
                  <button
                    onClick={() => importMutation.mutate(selectedItem.id)}
                    disabled={importMutation.isPending}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                  >
                    <Library className="w-4 h-4" />
                    导入图书馆
                  </button>
                )}

                {selectedItem.status === 'imported' && (
                  <div className="p-3 bg-green-50 text-green-700 rounded text-center">
                    <Check className="w-5 h-5 inline mr-2" />
                    已导入 (书籍 ID: {selectedItem.imported_book_id})
                  </div>
                )}

                {['failed', 'skipped'].includes(selectedItem.status) && (
                  <button
                    onClick={() => retryMutation.mutate(selectedItem.id)}
                    disabled={retryMutation.isPending}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="w-4 h-4" />
                    重新匹配
                  </button>
                )}

                {!['imported', 'skipped'].includes(selectedItem.status) && (
                  <button
                    onClick={() => skipMutation.mutate(selectedItem.id)}
                    disabled={skipMutation.isPending}
                    className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 flex items-center justify-center gap-2"
                  >
                    <SkipForward className="w-4 h-4" />
                    跳过此书
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <BookOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>选择左侧项目开始审核</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

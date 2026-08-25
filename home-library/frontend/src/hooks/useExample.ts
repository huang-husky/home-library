import { useState, useEffect } from 'react';

/**
 * 基础示例 Hook
 * 后续用于封装通用逻辑
 */
export function useExample() {
  const [value, setValue] = useState(0);

  useEffect(() => {
    // 示例逻辑
  }, []);

  return { value, setValue };
}

import { useState, useEffect } from 'react';

/**
 * デバイス判定フック
 * モバイルデバイス（max-width: 768px）かどうかを判定
 *
 * @returns {{ isMobile: boolean }}
 */
const useDeviceDetect = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 768px)');

    // 初期値をセット
    setIsMobile(mediaQuery.matches);

    // メディアクエリ変更時のハンドラ
    const handleChange = (e) => {
      setIsMobile(e.matches);
    };

    // リスナー登録
    mediaQuery.addEventListener('change', handleChange);

    // クリーンアップ
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return { isMobile };
};

export default useDeviceDetect;

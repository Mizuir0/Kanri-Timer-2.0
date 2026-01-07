import { useEffect } from 'react';

/**
 * 汎用モーダルコンポーネント
 *
 * @param {boolean} isOpen - モーダルが開いているか
 * @param {function} onClose - 閉じるボタンクリック時のコールバック
 * @param {string} title - モーダルタイトル
 * @param {ReactNode} children - モーダル内容
 */
const Modal = ({ isOpen, onClose, title, children }) => {
  // ESCキーで閉じる
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // スクロール防止
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* バックドロップ */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      ></div>

      {/* モーダルコンテンツ */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="閉じる"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
};

export default Modal;

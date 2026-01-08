/**
 * 秒数をMM:SS形式に変換
 * @param {number} seconds - 秒数
 * @returns {string} - MM:SS形式の文字列
 */
export const formatTime = (seconds) => {
  if (seconds < 0) seconds = 0;

  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);

  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

/**
 * ISO日時文字列を日本時間に変換
 * @param {string} isoString - ISO形式の日時文字列
 * @returns {string} - 日本時間の文字列
 */
export const formatDateTime = (isoString) => {
  if (!isoString) return '';

  const date = new Date(isoString);
  return date.toLocaleString('ja-JP');
};

/**
 * 時間差（秒）を表示形式に変換
 * @param {number} seconds - 時間差（秒）。正の値は押し、負の値は巻き
 * @returns {string} - 「+1:30 押し」「-0:45 巻き」「定刻通り」形式
 */
export const formatTimeDifference = (seconds) => {
  if (seconds === 0 || seconds === null || seconds === undefined) {
    return '定刻通り';
  }

  const absDiff = Math.abs(seconds);
  const minutes = Math.floor(absDiff / 60);
  const secs = absDiff % 60;
  const timeStr = `${minutes}:${secs.toString().padStart(2, '0')}`;

  if (seconds > 0) {
    return `+${timeStr} 押し`;
  }
  return `-${timeStr} 巻き`;
};

/**
 * 時間差に応じたTailwind CSSカラークラスを返す
 * @param {number} seconds - 時間差（秒）
 * @returns {string} - Tailwind CSSクラス
 */
export const getTimeDifferenceColor = (seconds) => {
  if (seconds > 0) return 'text-red-600';    // 押し
  if (seconds < 0) return 'text-green-600';  // 巻き
  return 'text-gray-600';                     // 定刻通り
};

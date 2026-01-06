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

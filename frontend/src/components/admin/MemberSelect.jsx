import { useEffect } from 'react';
import { useTimerStore } from '../../stores/timerStore';

/**
 * メンバー選択ドロップダウン
 *
 * @param {number} value - 選択されているメンバーID
 * @param {function} onChange - 変更時のコールバック
 * @param {string} label - ラベル文字列
 * @param {number[]} excludeIds - 除外するメンバーID（重複選択防止）
 */
const MemberSelect = ({ value, onChange, label, excludeIds = [] }) => {
  const { members, fetchMembers } = useTimerStore();

  // マウント時にメンバー一覧を取得
  useEffect(() => {
    if (members.length === 0) {
      fetchMembers();
    }
  }, [members.length, fetchMembers]);

  // 除外IDを除いたメンバーリスト
  const availableMembers = members.filter(
    (member) => !excludeIds.includes(member.id) || member.id === value
  );

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={value || ''}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        required
      >
        <option value="">選択してください</option>
        {availableMembers.map((member) => (
          <option key={member.id} value={member.id}>
            {member.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default MemberSelect;

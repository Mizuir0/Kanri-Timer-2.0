import { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import MemberSelect from './MemberSelect';
import Button from '../common/Button';
import { createTimer, updateTimer } from '../../services/api';

/**
 * タイマー追加・編集モーダル
 *
 * @param {boolean} isOpen - モーダルが開いているか
 * @param {function} onClose - 閉じる時のコールバック
 * @param {object|null} timer - 編集対象のタイマー（新規作成時はnull）
 */
const TimerFormModal = ({ isOpen, onClose, timer = null }) => {
  const isEditMode = timer !== null;

  // フォーム状態
  const [formData, setFormData] = useState({
    band_name: '',
    minutes: 15,
    member1_id: null,
    member2_id: null,
    member3_id: null,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  // 編集モード時、タイマーデータをフォームにセット
  useEffect(() => {
    if (isEditMode && timer) {
      setFormData({
        band_name: timer.band_name,
        minutes: timer.minutes,
        member1_id: timer.member1?.id || null,
        member2_id: timer.member2?.id || null,
        member3_id: timer.member3?.id || null,
      });
    } else {
      // 新規作成モード時はフォームをリセット
      setFormData({
        band_name: '',
        minutes: 15,
        member1_id: null,
        member2_id: null,
        member3_id: null,
      });
    }
  }, [isEditMode, timer, isOpen]);

  // フィールド変更ハンドラ
  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // バリデーション
  const validate = () => {
    if (!formData.band_name.trim()) {
      alert('バンド名を入力してください。');
      return false;
    }

    if (formData.minutes <= 0) {
      alert('予定時間は1分以上で指定してください。');
      return false;
    }

    if (!formData.member1_id || !formData.member2_id || !formData.member3_id) {
      alert('担当者3名を全て選択してください。');
      return false;
    }

    // 重複チェック
    const memberIds = [formData.member1_id, formData.member2_id, formData.member3_id];
    const uniqueIds = new Set(memberIds);
    if (uniqueIds.size !== 3) {
      alert('同じメンバーを複数回選択することはできません。');
      return false;
    }

    return true;
  };

  // フォーム送信
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      if (isEditMode) {
        // 編集
        await updateTimer(timer.id, formData);
      } else {
        // 新規作成
        await createTimer(formData);
      }

      onClose();
    } catch (error) {
      console.error('Timer form submit error:', error);
      const errorMessage =
        error.response?.data?.detail || 'タイマーの保存に失敗しました。';
      alert(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'タイマー編集' : 'タイマー追加'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* バンド名 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            バンド名
          </label>
          <input
            type="text"
            value={formData.band_name}
            onChange={(e) => handleChange('band_name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="例: Band A"
            required
          />
        </div>

        {/* 予定時間 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            予定時間（分）
          </label>
          <input
            type="number"
            value={formData.minutes}
            onChange={(e) => handleChange('minutes', Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1"
            max="120"
            required
          />
        </div>

        {/* 担当者1 */}
        <MemberSelect
          label="担当者1"
          value={formData.member1_id}
          onChange={(value) => handleChange('member1_id', value)}
          excludeIds={[formData.member2_id, formData.member3_id].filter(Boolean)}
        />

        {/* 担当者2 */}
        <MemberSelect
          label="担当者2"
          value={formData.member2_id}
          onChange={(value) => handleChange('member2_id', value)}
          excludeIds={[formData.member1_id, formData.member3_id].filter(Boolean)}
        />

        {/* 担当者3 */}
        <MemberSelect
          label="担当者3"
          value={formData.member3_id}
          onChange={(value) => handleChange('member3_id', value)}
          excludeIds={[formData.member1_id, formData.member2_id].filter(Boolean)}
        />

        {/* ボタン */}
        <div className="flex gap-3 pt-4">
          <Button
            type="submit"
            variant="primary"
            disabled={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? '保存中...' : isEditMode ? '更新' : '作成'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isSubmitting}
            className="flex-1"
          >
            キャンセル
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default TimerFormModal;

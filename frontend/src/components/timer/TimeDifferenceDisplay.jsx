import { useTimerStore } from '../../stores/timerStore';

const TimeDifferenceDisplay = () => {
  const { totalTimeDifferenceDisplay } = useTimerStore();

  if (!totalTimeDifferenceDisplay) {
    return null;
  }

  // 押し/巻き/定刻で色を変える
  const getColorClass = () => {
    if (totalTimeDifferenceDisplay.includes('押し')) {
      return 'text-red-600 bg-red-50 border-red-200';
    } else if (totalTimeDifferenceDisplay.includes('巻き')) {
      return 'text-green-600 bg-green-50 border-green-200';
    } else {
      return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`p-4 border-l-4 ${getColorClass()}`}>
      <div className="text-center">
        <p className="text-sm font-medium">全体の進行状況</p>
        <p className="text-2xl font-bold tabular-nums mt-1">{totalTimeDifferenceDisplay}</p>
      </div>
    </div>
  );
};

export default TimeDifferenceDisplay;

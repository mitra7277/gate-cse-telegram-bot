from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import Attempt, User, IncorrectAnswer

def get_user_stats(db: Session, user_id: int) -> dict:
    """Calculates overall stats for a user."""
    total_attempts = db.query(Attempt).filter(Attempt.user_id == user_id).count()
    correct_attempts = db.query(Attempt).filter(Attempt.user_id == user_id, Attempt.is_correct == True).count()

    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0.0

    user = db.query(User).filter(User.id == user_id).first()

    return {
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "accuracy": round(accuracy, 2),
        "current_streak": user.current_streak if user else 0,
        "highest_streak": user.highest_streak if user else 0
    }

def get_weak_areas(db: Session, user_id: int) -> list:
    """Identifies topics where the user has the most incorrect answers."""
    weak_areas = (
        db.query(Attempt.topic, func.count(Attempt.id).label('incorrect_count'))
        .filter(Attempt.user_id == user_id, Attempt.is_correct == False)
        .group_by(Attempt.topic)
        .order_by(func.count(Attempt.id).desc())
        .limit(3)
        .all()
    )

    return [{"topic": area.topic, "incorrect_count": area.incorrect_count} for area in weak_areas]

def format_progress_report(stats: dict, weak_areas: list) -> str:
    """Formats the progress report for Telegram."""
    report = (
        "📊 *Your Progress Report*\n\n"
        f"📝 Total Attempts: {stats['total_attempts']}\n"
        f"✅ Correct: {stats['correct_attempts']}\n"
        f"🎯 Accuracy: {stats['accuracy']}%\n\n"
        f"🔥 Current Streak: {stats['current_streak']}\n"
        f"🏆 Highest Streak: {stats['highest_streak']}\n\n"
    )

    if weak_areas:
        report += "*Areas to Improve:*\n"
        for area in weak_areas:
            report += f"- {area['topic']} ({area['incorrect_count']} mistakes)\n"
    else:
         report += "Keep up the good work! No specific weak areas identified yet."

    return report

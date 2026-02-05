from __future__ import annotations

from hot_trigger.models import AnalysisArtifact, DecisionArtifact, DecisionVerdict, ScoreBreakdown, TriggerEvent


class DeterministicDecider:
    def decide(self, event: TriggerEvent, analysis: AnalysisArtifact) -> DecisionArtifact:
        domain_relevance = self._domain_relevance(event, analysis)
        differentiation_space = self._differentiation_space(analysis)
        participation_cost = self._participation_cost(analysis)
        risk_compliance = self._risk_compliance(analysis)
        timeliness = self._timeliness(event)

        score_breakdown = ScoreBreakdown(
            domain_relevance=domain_relevance,
            differentiation_space=differentiation_space,
            participation_cost=participation_cost,
            risk_compliance=risk_compliance,
            timeliness=timeliness,
        )
        ride_score = round(
            domain_relevance * 0.25
            + differentiation_space * 0.2
            + participation_cost * 0.15
            + risk_compliance * 0.2
            + timeliness * 0.2
        )

        if ride_score >= 75:
            verdict = DecisionVerdict.go
        elif ride_score >= 45:
            verdict = DecisionVerdict.wait
        else:
            verdict = DecisionVerdict.no

        rationale = [
            f"领域相关性 {domain_relevance}/100，基于关键词与标签命中。",
            f"差异化空间 {differentiation_space}/100，来源于可执行角度数量。",
            f"参与成本 {participation_cost}/100，偏向评论/跟帖等轻量动作。",
            f"风险与合规 {risk_compliance}/100，风险标记越少越高。",
            f"热度时效性 {timeliness}/100，rank/heat 越高越适合立即参与。",
        ]

        return DecisionArtifact(
            event_id=event.event_id,
            ride_score=ride_score,
            verdict=verdict,
            score_breakdown=score_breakdown,
            rationale=rationale,
            suggested_comment=self._suggest_comment(analysis),
            suggested_post_outline=self._suggest_outline(analysis),
        )

    def _domain_relevance(self, event: TriggerEvent, analysis: AnalysisArtifact) -> int:
        keyword_hits = len(event.delta.get("keywords", []))
        tag_hits = min(len(event.unit.tags), 3)
        return min(100, 35 + keyword_hits * 20 + tag_hits * 15)

    def _differentiation_space(self, analysis: AnalysisArtifact) -> int:
        return min(100, 30 + len(analysis.angles) * 15)

    def _participation_cost(self, analysis: AnalysisArtifact) -> int:
        lightweight_modes = {"评论", "comment", "跟帖", "duet", "stitch"}
        mode_hit = sum(1 for mode in analysis.participation_modes if mode.lower() in lightweight_modes)
        return min(100, 45 + mode_hit * 15)

    def _risk_compliance(self, analysis: AnalysisArtifact) -> int:
        if not analysis.risk_flags:
            return 90
        return max(10, 90 - len(analysis.risk_flags) * 20)

    def _timeliness(self, event: TriggerEvent) -> int:
        rank_score = 50
        if event.unit.rank is not None:
            rank_score = max(20, 100 - event.unit.rank * 3)
        heat_score = int(event.unit.heat_score or 50)
        return min(100, round(rank_score * 0.6 + heat_score * 0.4))

    def _suggest_comment(self, analysis: AnalysisArtifact) -> str:
        angle = analysis.angles[0] if analysis.angles else "补充一个实用观点"
        return f"这个话题确实有共鸣，我补充一个角度：{angle}。"

    def _suggest_outline(self, analysis: AnalysisArtifact) -> list[str]:
        first_angle = analysis.angles[0] if analysis.angles else "核心观点"
        return [
            f"开场：{analysis.summary or '复盘热点现象'}",
            f"原因拆解：{analysis.why_trending or '解释背后的传播机制'}",
            f"差异化表达：围绕“{first_angle}”展开",
            "行动建议：给读者一个可立即执行的方法",
        ]

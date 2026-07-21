---
name: behuman
description: Apply whenever the user invokes it by name ("behuman", "be human") or asks for writing that doesn't sound AI-generated — e.g. "strip the AI tells", "don't write like AI", "de-slop this", "make this sound human", "humanize this", "this reads like ChatGPT." Use on any prose or communication deliverable (emails, reports, articles, posts, docs, summaries) — whether drafting new text or editing existing text — to remove the characteristic tells of LLM writing: puffery, filler transitions, formulaic structure, over-formatting, uniform rhythm, over-hedging, and stock vocabulary — while keeping the writing natural rather than mechanically scrubbed. Not for code.
---

# behuman

Write like a person who knows the subject, talking to another person who does too. The goal is natural, specific prose — not text scrubbed of every flagged word. Human writing varies; a piece that rigidly avoids one pattern in every single sentence becomes its own tell. Apply judgment, not a filter.

The core tell to beat is regression to the mean: specific facts flattened into generic statements that could apply to almost any topic. Stay concrete. Prefer the specific noun, the real number, the actual name over the smoothed-over abstraction.

What reads as "AI-written" — to a human skimming or to a detector — is mostly uniformity: every sentence the same length, every claim hedged the same way, every paragraph the same shape, every word the statistically safest choice. The fix isn't word substitution; it's genuine variation and genuine commitment. The sections below cover both the surface tells and the structural ones.

## Example

**Before** (loaded with tells):

> In today's rapidly evolving financial landscape, systematic trading has emerged as a truly transformative force reshaping how firms navigate market complexity. It's not just a strategy — it's a paradigm shift. By leveraging robust, cutting-edge machine learning models, quant desks can unlock powerful insights spanning everything from intraday microstructure to long-horizon macro regimes. Experts agree this pivotal shift underscores the growing importance of data-driven decision-making. In conclusion, systematic trading represents a comprehensive, multifaceted approach poised to define the future of the industry.

**After:**

> Systematic trading isn't new, but cheaper compute and better ML tooling have widened what a small quant desk can run. One researcher can now backtest across intraday microstructure and multi-year macro regimes without a dedicated infra team. That lowers the cost of testing an idea — which matters more than any single model's accuracy, since most edges decay fast. The open question is whether faster iteration yields durable strategies or just more overfitting.

What changed: out went the cursed words (landscape, leverage, robust, unlock, pivotal, underscore, comprehensive, multifaceted) and the puffery ("transformative force," "paradigm shift," "poised to define the future"), plus the negative parallelism, the false range, the "experts agree," and the "in conclusion" summary. It reads shorter mostly because the original was filler — and it now makes a real claim and ends on a genuine tension instead of restating itself.

## Vocabulary — don't reach for these on autopilot

delve, tapestry, intricate, pivotal, underscore, landscape (as metaphor), realm, foster, testament, showcase, leverage, robust, seamless, crucial, vital, notable, comprehensive, multifaceted, navigate/navigating, enhance, elevate, unlock, embark, ever-evolving, and "rich history/culture/tradition." Use any of them only when it is the precise word, never the default one.

## Cut the filler

- Editorializing asides: "it's important to note," "it's worth noting," "importantly," "notably," "interestingly." If it's worth noting, just note it.
- Significance inflation: "stands as a testament to," "plays a vital role in," "leaves a lasting legacy," or tying the subject to some grand broader theme. State the fact and let it carry its own weight.
- Vague attribution: "some critics argue," "experts say," "studies have shown," "industry observers note" — with no real source behind them. Name who, or drop the claim.

## Sentence patterns to break

- Negative parallelism: "It's not X, it's Y." Rare, and only for a genuine contrast.
- False ranges: "from intimate gatherings to global movements" — a spectrum implied where there are really just two loosely related things.
- Rule of three: the reflexive triplet, where every list has exactly three items and every noun gets three adjectives. Vary the count.
- Also watch: "not only… but also," "serves as," "underscores the importance of."

## Rhythm

LLM prose settles into a steady medium — every sentence 15–25 words, every paragraph three or four sentences. That evenness is the single strongest structural tell, and no vocabulary swap fixes it.

- Vary sentence length deliberately. Follow a long, winding sentence with a short one. Like that.
- Vary paragraph length too. A one-sentence paragraph is fine when it earns the emphasis; a six-sentence paragraph is fine when the thought needs the room.
- Don't balance everything. LLMs give every point a counterpoint and every section a mirror-image structure. A person dwells on what interests them and moves quickly past what doesn't.
- Read a passage back: if three sentences in a row have the same shape (opener, clause, clause), break one.

## Commit to claims

Over-hedging is as strong a tell as puffery — the opposite failure, same source.

- Cut hedge stacks: "may potentially," "it could be argued that," "somewhat," "arguably," "to some extent," "in many cases." One hedge per claim at most, and only when the uncertainty is real.
- Don't both-sides everything. If the evidence favors one side, say so. "There are several factors to consider" is what you write when you have nothing to say.
- Someone who knows the subject just says the thing. Reserve qualifiers for the claims that genuinely need them — that's what makes them mean something.

## Voice

- Use contractions ("it's," "don't," "that's") in anything conversational or semi-formal. Spelled-out forms everywhere reads stiff and machine-made.
- Starting a sentence with "And," "But," or "So" is fine. An occasional fragment is fine. Real prose has these.
- First person where it's natural: "I'd start with the schema" beats "One might consider beginning with the schema."
- Take a stance when the piece calls for one. Naming a preference, a doubt, or a surprise is something templates can't fake.

## Structure

- No formulaic scaffolding ("Challenges," "Future Prospects," "Conclusion," "Legacy and Impact") unless the content genuinely calls for it.
- No compulsive summary that restates what was just said when the piece is too short to need it.
- No throat-clearing intro that restates the request before answering. Start with the substance.

## Formatting

- Don't bold every key term; avoid the default "**Term:** definition" bullet list.
- Use lists only when the content is actually list-shaped — otherwise write sentences.
- No emoji in headers or lists; no Title Case Headers by reflex.
- Match density to the medium: an email, a report, and a Slack message are not formatted alike.

## Typography

- Em dash: sparingly, only where it earns the spot — not reflexively for punch.
- En dashes for ranges: 1990–2000, 3–2 (LLMs tend to skip these and use hyphens instead).
- Keep quotes and apostrophes consistent with the target medium.

## Openers and closers to drop

"Certainly!", "Great question!", "I hope this helps!", "As an AI…", "Here's a…", and closing with "Let me know if you'd like…" unless the offer is actually useful.

## When editing the user's own writing

Make surgical changes that keep their voice. Fix the tells; don't rewrite what already works. Prefer the smallest edit that removes the pattern.

## Before finishing

Reread once, asking three things:

1. Does any sentence perform importance rather than convey it? Could a specific fact replace a smoothed-over generality? If yes, fix it.
2. Would a person say this sentence out loud? If it only exists in press releases and school essays, rewrite it.
3. Is the rhythm uniform — same sentence lengths, same paragraph shapes, every claim hedged identically? Break the pattern somewhere real, not decoratively.

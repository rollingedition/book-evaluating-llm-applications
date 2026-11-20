---
chapter_id: build-the-test-set
---

# Build a test set you can defend, and read public benchmarks

By the end of this chapter you can build a test set whose score tells you something, check its schema and coverage with code, and say what a public benchmark score does and does not tell you about your own assistant. You will also see how a multiple-choice score can be impossible to tell apart from a habit of answering the same way.

Here the test set belongs to the sablefile assistant, a retrieval step and a model that answers questions from the tool's docs. Every number this book reports about the assistant comes from a set of questions with reference answers, so the set decides how much a score is worth. The book guards against three faults. If every question has an answer in the docs, an assistant that always answers will look good. If the questions reuse the docs' own sentences, retrieval matches on words and looks right. If the set is tuned until the score rises, the score records the tuning. The set is also the only place the questions are written down, so a fault in it can go unseen, and a score built on it inherits the fault without any sign of it.

This chapter builds the set the book uses and checks it with code. It then reads two public benchmarks, GSM8K and TruthfulQA, which many readers will have seen quoted, and says what their scores can still show. The sections follow the questions a team would ask in turn: what the set is for, how it is built and checked, how it is split, and what a public score adds.

## What a test set is for {#what-a-test-set-is-for}

A test set is a fixed set of questions, paired with the answers you would accept, that stands in for the questions users will ask. Its job is to be asked the same questions each time something changes, so that a difference in score comes from the change and not from the questions. It does that job only while it stays fixed. This set was written from the docs rather than sampled from users, so it stands in for them and does not reproduce them.

Each row is an **item**: one test question with the fields a scorer needs. The item is the unit of every count in this book, so a pass rate is always a share of items, and its denominator says which ones. Each item has a **reference answer**, which the scorer compares a reply with, and **supporting sections**, the parts of the docs that a correct answer rests on. The reference answers are written labels. The book's own drafting agents wrote them from the docs, a second pass checked them against the docs, and a script checks the file's shape and section IDs. They are not human labels, and the book does not call them that.

Each item also has a **kind**, which says what a correct reply looks like. A set built from one kind tests one skill, so this set mixes four kinds on purpose. It should also look like the questions users bring. Users ask things the docs cannot answer, and a set with only answerable questions would reward an assistant that never declines.

The set is small on purpose. It holds {{out:check-item-schema:items}} items, which a reader can check by hand, and each one has a reference answer that a second pass checked against the docs. We keep it small enough to read, because a set nobody reads can only measure its own mistakes. A score is only as good as the set behind it, and the set is what two people argue about when they disagree on whether a change helped. Keep it readable, keep the reasons for each item written down, and do not add items only because a score looks wrong, since that picks items for their result.

A test set is never training data. Nothing in it teaches the assistant, and the assistant never sees a reference answer while the set is being built. If someone tunes against the answers, the set stops being a test and becomes a target, which is what the [rule on dev and held-out](#dev-and-held-out) is for.

**Working rule:** Write the set before you change anything you will measure with it, and keep its file under version control, so that every comparison names the items it used. A set you edit after seeing the scores measures your edits, not the assistant.

## The item schema {#the-item-schema}

The set has to load before anything is scored. The file holds one JSON object per line, and a loader validates each one with pydantic, a Python library that checks values against a declared shape. This book pins pydantic {{version:pydantic}}. The fields are these:

- `id`: `q-` and four digits, unique, and never changed once written.
- `question`: one to 400 plain characters.
- `version`: the docs version the question asks about.
- `kind`: one of the four kinds.
- `reference_answer`: the answer, or nothing for an unanswerable item, where the right reply is to decline.
- `supporting_sections`: the version and section ID pairs that the answer rests on.
- `split`: `dev` or `held-out`.
- `planted` and `planted_why`: whether the item is a planted trap, and which one.
- `twin_of`: the ID of the item that asks the same question about another version, if there is one.

The loader sets `extra="forbid"`, so an unknown field is an error and not a field that is quietly ignored. A typo in a field name would otherwise produce a set that looks right and scores wrong. Errors are reported row by row, so one bad row does not hide the rest.

Shape checks cannot see across rows, so the cross-item rules in the book's `lib/testset.py` do that work. They check that IDs are unique, that each twin names its partner back, asks for another version, is version-dependent and sits in the same split, and that every false-premise item is unanswerable. They check that every supporting section exists for the version it names, that no reference answer repeats eleven words in a row from a section, and that the counts match the design.

Each of these rules is a contract that anyone who adds or edits an item has to pass. The check prints each broken rule. It exits without an error code whether or not it finds one, so it stops nothing by itself, and the build has to treat a printed problem as a failure.

The reference answer needs the most care of all, because every reply is compared with it. A reference that is wrong in a consistent direction makes the score wrong in that direction, and no shape rule can catch a well-formed wrong answer. That is why each reference is written with the sections it rests on, so a reader can check the claim against the docs in a few minutes rather than take the author's word.

Twins can drift into different splits when they are written at different times, and then the dev part tunes on a question the held-out part checks. The cross-item rules catch that, so the twins stay together.

The schema check below runs both groups of rules and prints the problem count, with the counts by kind and by split.

[Example: check-item-schema](../examples/check-item-schema.py)

The set holds {{out:check-item-schema:items}} items, and the rules find {{out:check-item-schema:problems}} problems. A clean run means the rows parse, the references point at sections that exist, and the counts match the design. It shows the set's shape only. It does not mean the questions are good, that the reference answers are right, or that a planted item catches an assistant. Those claims need a reader, and the rest of this chapter describes how the set was built so that a reader can check them.

**Working rule:** Run the schema check in the build and treat any printed problem as a failure, and read a sample of items by hand before you trust the set.

## Kinds and coverage {#kinds-and-coverage}

Each kind tests something the assistant must do. An answerable item has docs that answer it fully, so the assistant must answer and agree with the reference, and its citations are checked on their own. A refusal there is a false refusal. An unanswerable item has docs that do not say, so the right reply is the decline phrase, exactly. Any other reply is a false answer, and these items are what stop an assistant that always answers from scoring well. [The chapter on declining](declining-when-the-docs-dont-say) covers the phrase. A version-dependent item names the version it asks about, and its reply must match that version's reference. An ambiguous item admits two readings, and the reference holds one answer per reading. A reply must answer each reading the docs support, and a partial answer fails.

The kinds table below prints the set by kind and by split.

[Example: kinds-by-split](../examples/kinds-by-split.py)

The table prints the split by kind that the design fixes: each kind is divided between dev and held-out in about the same proportion, and the planted items are split the same way. Its last line gives the item count, {{out:kinds-by-split:items}}, which matches the schema check. By kind, the set holds:

- answerable: {{out:check-item-schema:kind answerable}} items;
- unanswerable: {{out:check-item-schema:kind unanswerable}} items;
- version-dependent: {{out:check-item-schema:kind version-dependent}} items;
- ambiguous: {{out:check-item-schema:kind ambiguous}} items.

Coverage asks which parts of the tool the set exercises. The sablefile tool has six behaviours that an assistant must get right, named B1 to B6: what `sablefile sync` does with no flag, the exit status of `check` when a file has drifted, the syntax of `ignore` entries, the lock file's format, the placeholder syntax, and the retry count for remote fetches. The wrong-version answers that [chapter 2](read-the-outputs) found fall on these behaviours: q-0021 on B2, q-0023 on B3 and q-0029 on B1.

The coverage check stops if its mapping misses an item.

[Example: behaviour-coverage](../examples/behaviour-coverage.py)

Each behaviour's count is one line of output:

- B1, the default of `sync`: {{out:behaviour-coverage:B1 items}} items.
- B2, the exit status of `check`: {{out:behaviour-coverage:B2 items}} items.
- B3, `ignore` syntax: {{out:behaviour-coverage:B3 items}} items.
- B4, the lock file: {{out:behaviour-coverage:B4 items}} items.
- B5, placeholder syntax: {{out:behaviour-coverage:B5 items}} items.
- B6, retries for remote fetches: {{out:behaviour-coverage:B6 items}} items.

One item carries two behaviours, so the six counts add up to one more than the items that carry any. Items with no behaviour are still part of the set. Here {{out:behaviour-coverage:items with no behaviour}} of the {{out:behaviour-coverage:items}} items carry none.

**Working rule:** Count coverage for each behaviour before you quote a score for it, and treat a behaviour with only a few items as untested. Passing those items shows that one behaviour, and nothing about the rest of the tool.

### Planted items and their traps {#planted-items}

A planted item is written to break an assistant in one named way. Each carries a reason from a fixed list of five:

- `false-premise`: the question asks about a flag or key that the asked version does not have. The right reply is the decline phrase, so planted false premises are always unanswerable.
- `near-miss-term`: a term one version renamed, or a term the docs use for another concept.
- `version-swap`: the question uses another version's wording, so an assistant that matches wording answers for that version.
- `stale-answer`: the answer sits under a section ID that a version filter removes, so a filter that is too strict misses it.
- `ambiguous-target`: a pronoun or a phrase such as "the file" has no clear referent without the sections.

A planted item is useful because its failure is named. If the assistant fails it, a reader knows which failure happened. Planted items are counted with their kind, so a planted false premise is also unanswerable. The set holds {{out:check-item-schema:planted}} planted items, about one in five. Planted items are not split out in the metric tables, and no chapter in this book reports results trap by trap.

**Working rule:** Plant an item only for a trap you can name from the list. Write down the wrong reply it should catch, and check against the cited sections that the wrong reply is wrong, before the item enters the set.

### Synthetic items and what they hide {#synthetic-items}

These items were written from the docs, and the book builds them against two traps. The first is copying. A question that repeats a section's sentence gives retrieval a match on words it finds at once, so the test then measures word matching and not answering. The copy check stops a reference that repeats eleven words of a section, but it covers reference answers only, not questions. The rule for writing is to ask each question the way a user would, in the user's words and not the docs'.

The second trap is a reference that is true for two versions, so a reply that describes the other version passes. A version-dependent item names its version, and its twin pairs the same question with a second version, so no reply is right for both by accident.

**Working rule:** Ask each question the way a user would, from the docs but not in their sentences, and read each question against its sections before the set is frozen, since the copy check does not read questions. For a behaviour that changed between versions, name the version in the question and write its twin.

## Dev and held-out {#dev-and-held-out}

The set is split in two, because a score tuned on the questions it is measured with does not show progress. Dev may be tuned on, and held-out is used once, to report a result. The split is stratified, so that each kind appears in both parts in about the same proportion. Without that, one part could hold most of the unanswerable items, and the two scores would then measure different sets. The set holds {{out:check-item-schema:split dev}} dev items and {{out:check-item-schema:split held-out}} held-out items, and each row's `split` field records which part it belongs to. The twenty items that [chapter 1](measure-before-you-change) measures are dev items, so its rates are dev rates.

Only dev may be tuned on. Prompt wording, the number of sections retrieved, the version filter and the wording of the judge's rubric may all be chosen from dev results. Once a setting is chosen, it is frozen before held-out runs. Held-out runs once for each variant, in the chapter that compares the variants, and its numbers are the ones a chapter quotes. A recording's manifest says whether anything in it was tuned on held-out, and that answer must be no.

Dev has a job that held-out does not. It is where failures are read, so that a reader can form a hypothesis about why the assistant fails. A hypothesis formed on dev is a claim to test on held-out, not a result. Reading dev failures to choose a setting is allowed. Reading held-out failures to choose a change is not.

A split is only as clean as its record. Each row's split is written once, when the item is written, and it does not move with the scores. A split that changes after the scores are in is not a split.

Held-out is small, and a score on it is one number with an interval around it. A comparison on held-out therefore needs paired items, one verdict per item for each variant, and an interval over those pairs. [The chapter on intervals and sample size](intervals-and-sample-size) builds that comparison, and this chapter only needs the rule it rests on.

One more rule keeps the split honest. A question may be corrected only when its reference answer or its sections are wrong. It may never be changed because the assistant fails it. Otherwise the set would measure the assistant's last failure, and the score would rise each time someone fixed a failure by editing the test.

**Working rule:** Tune only on dev, freeze every setting before you open held-out, and run held-out once for each comparison. A held-out score that you read before a change, and then lifted by changing something, is a dev score, and you should say so.

## Public benchmarks {#public-benchmarks}

A public benchmark is a set of questions and answers someone else published. It does not measure the sablefile assistant, and its score depends on the prompt, the sampling and the parser.

Both samples are seeded samples of one hundred items, and their cards were read on November 20, 2026. Both recordings come from Qwen3-4B-Instruct-2507, the book's assistant and judge, in its Q4_K_M GGUF build, run on a CPU with greedy decoding. Replies were capped at {{out:score-gsm8k:token cap}} tokens for GSM8K and {{out:score-truthfulqa:token cap}} for TruthfulQA.

**Working rule:** Quote a public score only beside its sample, model build, prompt, parser, reply cap and interval, and never beside a published number.

### GSM8K {#gsm8k}

GSM8K is grade-school math word problems, each with a worked solution that ends in one number. The score is an exact match on that number. The prompt asks for a "Final answer:" line the scorer never reads. It takes the number after the last `####` marker in the reply, or else the last number in the reply. No reply contains `####`, so every verdict came from the last number, which for a finished reply is its "Final answer:" number. The paper describes 8.5K problems, with 1K for testing ([Cobbe and colleagues, 2021](https://arxiv.org/abs/2110.14168)). The [dataset card](https://huggingface.co/datasets/openai/gsm8k) gives its second split 1,319 rows, which the viewer calls "test" and the splits table calls "validation". The book does not reconcile them, and the sample uses the viewer's "test" split. The card gives the licence as MIT.

[Example: score-gsm8k](../examples/score-gsm8k.py)

The parser found a number in {{out:score-gsm8k:readable}} replies. The accuracy is {{out:score-gsm8k:accuracy}}. The interval is {{out:score-gsm8k:accuracy interval}}, so a gap of a few points between two configurations would fall inside it.

{{out:score-gsm8k:no final answer line}} replies have no "Final answer:" line, and each stops mid-solution. Among the wrong replies, {{out:score-gsm8k:no final answer line among wrong}} have no such line. A cut-off reply is scored by its last number, often an intermediate value, so the score partly measures the cap rather than only the reasoning. The wrong example, gsm8k-test-0214, is one of these: the scorer read {{out:score-gsm8k:wrong parsed}}, and the reference is {{out:score-gsm8k:wrong reference}}.

The cap also touches the right replies: {{out:score-gsm8k:no final answer line among right}} stops before its final line, and the scorer marks it right only because its last number is the answer.

The book uses GSM8K to check the harness, not to rank the assistant.

**Working rule:** Count the replies with no final line before you quote a score, and compare two configurations only with a paired comparison that clears its interval.

### TruthfulQA {#truthfulqa}

TruthfulQA asks questions on which people often answer falsely, such as a common myth. Its paper describes 817 questions in 38 categories ([Lin and colleagues, 2022](https://arxiv.org/abs/2109.07958)). The book uses its multiple-choice version, MC1: exactly one option is correct, and the model answers with a letter. The [dataset card](https://huggingface.co/datasets/truthfulqa/truthful_qa) has one split, named validation, and gives the licence as Apache-2.0.

[Example: score-truthfulqa](../examples/score-truthfulqa.py)

The parser read a letter from {{out:score-truthfulqa:readable}} replies. The accuracy is {{out:score-truthfulqa:accuracy}}. The interval is {{out:score-truthfulqa:accuracy interval}}.

The number of unreadable replies is {{out:score-truthfulqa:unreadable}}. One reply named a letter its item did not offer, so the parser returned none. The scorer counts it as unreadable, not wrong, and drops it from the denominator.

In every item the correct option comes first, as in the source. The order check confirms it: the correct option is first in {{out:score-truthfulqa:correct option first}} of the items. The replies chose the first option in {{out:score-truthfulqa:chose first option}} of the readable items.

The chance share averages one over each item's option count. A random choice would pick the first option in {{out:score-truthfulqa:chance first option}}.

Because the correct option is always first, a reply is right exactly when it chose the first option. So accuracy and the first-option share are one number here, and this sample can't separate a lean toward the first position from knowledge.
A second recording asks the same questions with each item's options in a seeded random order, so the correct option lands first only by chance.

[Example: score-truthfulqa-shuffled](../examples/score-truthfulqa-shuffled.py)

The accuracy is {{out:score-truthfulqa-shuffled:accuracy, shuffled options}}. The interval is {{out:score-truthfulqa-shuffled:accuracy interval, shuffled options}}.

The reply chose the first option in {{out:score-truthfulqa-shuffled:chose first option}}. A random choice would pick the first option in {{out:score-truthfulqa-shuffled:chance first option}}. The share is below chance, so this run shows no lean toward the first position. The correct option landed first in {{out:score-truthfulqa-shuffled:correct option first after shuffling}}, close to chance, so the shuffle worked.

Against the unshuffled run, item by item, the comparison covers {{out:score-truthfulqa-shuffled:paired items}} items. The difference, shuffled minus unshuffled, is {{out:score-truthfulqa-shuffled:difference, shuffled minus unshuffled}}. Its interval is {{out:score-truthfulqa-shuffled:95% interval of the difference}}. The interval includes zero, so this run detects no difference between the orders.

This score answers a different question from the assistant's task, and it does not measure [contamination](#contamination).

**Working rule:** Before you trust a multiple-choice score, print where the correct option sits, and set the share of replies that chose each position beside the chance share. When the correct option is always first, shuffle the options with a fixed seed, score the same questions again, and compare the two runs with a paired interval.

### Contamination {#contamination}

Contamination is when a benchmark's items or answers appear in training data, so a score can reflect memory rather than ability. This chapter measures neither sample.

One preprint compares a model's likelihood on canonical and shuffled item orders. Its authors find little pervasive contamination in five public models ([Oren and colleagues, 2023](https://arxiv.org/abs/2310.17623)), though the test needs log-probabilities and items that can be reordered.

The chapter made these decisions:

- Every item has a reference answer, supporting sections and a kind, and a schema check runs before any score.
- Dev is tuned on, and held-out runs once for each comparison.

**Working rule:** Name contamination beside every public score, and never present a benchmark score as the model's ability.
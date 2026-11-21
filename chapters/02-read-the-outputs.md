---
chapter_id: read-the-outputs
---

# Read the replies to find what to measure

By the end of this chapter you can read a set of replies from an assistant, sort what is wrong with each one into a failure mode, and say which of those failures a check can see.

Chapter 1 ended on a limit: twenty items can find broken answers, but they can't rank two prompts. The assistant in this book answers from three versions of sablefile's docs, 1.0, 1.1 and 2.0, and a question about one version can get an answer that is right for another. A pass rate counts every such failure the same way and names none of them. A team that measures only with a pass rate therefore writes its checks for the failures it expects, and the failures it doesn't expect go unchecked. Reading the replies first is how you find the second kind. Chapter 1's interval says how far a score can be trusted. This chapter asks what each variant gets wrong, which a score can't say.

Reading before counting has support outside this book. [Chapter 1](measure-before-you-change) cited Shankar and colleagues' [*Who Validates the Validators?*](https://arxiv.org/abs/2404.12272) (2024) for the point that people refine their grading criteria while they grade outputs. That paper is mainly a system, EvalGen, and its user study of nine practitioners is the part this chapter relies on. The drift the study records happened while people graded outputs. That a change to the pipeline can make the criteria drift is the authors' discussion, not a finding of the study. It is one study, so this chapter treats it as a caution, not as a result the book measures.

This chapter uses the {{out:tally-failure-modes:dev items}} dev items, the split of the test set this book works with while it develops its measures. It reads only the dev items, so nothing here is tuned to the held-out items, and the held-out decline counts appear in [chapter 10](declining-when-the-docs-dont-say). The reading produces three things: a note on each reply, a count of the defects those notes fall into, and a candidate check for each defect. Every reply here is a recording made once for each variant and replayed by the examples, so the reading is the same on every run. Quotes of replies come from the recorded outputs, and the reference answers are printed beside their items, so any line the prose quotes from them can be found in the example's output. The notes sit in a data file that the tally example reads.

Throughout, a reply counts as right when it gives the reference answer, or when it declines because the reference says the docs don't say. Its citations are checked on their own, by the citation check in [chapter 1](measure-before-you-change#citations-in-code) and the checks in [chapter 4](checks-in-code). Anything else is a failure, and the rest of the chapter says which kind. The same steps work on a replay file of your own. Group its replies by kind, read each one against its reference, code each by its main defect, and write one candidate check per mode. This chapter does that for the sablefile replies, so you can follow each step on data you can open.

This chapter doesn't choose the checks or write a judge's rubric, and it doesn't estimate how often each mode happens in real use. Those come in later chapters, and each one relies on the modes named here.

## What the replies look like {#what-the-replies-look-like}

Three variants of the assistant answered the same dev items, and every comparison in this chapter sets one variant's replies beside another's. The baseline is the setup chapter 1 measured. It retrieves sections only from the version the question asks about, so its context holds one version's docs. The unfiltered variant drops the baseline's version filter. Its context can hold sections from all three versions, each marked with its version, so the model can see a mismatch and can also copy the wrong version's text. The second-model variant keeps the baseline's prompt and hands the answer to a smaller model, Qwen3 with 0.6 billion parameters in an 8-bit build. The prompt is the same, so a difference from the baseline comes from the model, not the prompt.

Each dev item has a kind, and the kind says what a right reply looks like. An [answerable item](#the-twenty-items) is one the docs answer. An [unanswerable item](#the-twenty-items) asks for something the docs don't say, and the right reply is a decline in the words the assistant was given: "The docs don't say." A version-dependent item has an answer that changes with the version asked about, so the same question asked of two versions can have two right answers. An ambiguous item can be read two ways, and the docs answer each reading. Some items are [planted](#the-twenty-items), written to catch one specific mistake. The output gives each planted item its reason, which is one of a false premise, a near-miss term, a version swap, a stale answer or an ambiguous target. A reply that fails a planted item shows whether the assistant made the mistake that item was written for.

Reading one item takes three steps. Start with the question and its version, since a reply is right only for the version it names. Then read the reference answer, which is the author's statement of what a right reply says. Then read the three replies against it, one at a time. Only after that does a reader group the replies or count them.

The example that follows is where the chapter starts. It prints every dev item with its reference answer and each variant's reply, grouped by kind and sorted by ID, so the three replies to one question sit on adjacent lines. Read across an item's lines, not down one variant's column. The variants fail in different ways on the same question, and that difference is what to see. Each reply is cut to its first 120 characters, and its line says whether the reply declined and what it cited. A reply that holds the decline phrase inside other text is marked as a phrase, not a decline, so you can see where the parser draws the line.

[Example: read-replies-dev](../examples/read-replies-dev.py)

Take item q-0005. It asks whether sablefile 2.0 still reads sablefile.lock in the project root, and it is a planted near-miss term, a name close to one the docs use, which catches a careless reply. The baseline says no and cites a section about upgrading. The reference answer says that 2.0 falls back to the file, with a warning, so the baseline's no is wrong. The unfiltered and second-model variants both decline, and the docs do answer the question, so their declines are wrong as well.

The three replies to q-0005 fail in two different ways. A decline on an answerable item and a confident wrong answer are different failures, and a check that catches one doesn't catch the other. A pass rate would count all three replies as failures and lose that difference. The note on this reply in the data file begins "says 2.0 never reads sablefile.lock; reference says it falls back to it with a warning." Each note says what the reply did and what the reference says, in one sentence, so the grouping that follows rests on something a reader can check. A count can come from different defects, and two replies that both fail a pass rate can be different failures. That is why the replies come before the count.

The comparison has limits, and they bound what the counts can claim. The dev items were written to probe the assistant, and the planted items are not a random sample of what users ask. So the counts say which variant fails in which way on these items. They don't say how often a user would meet each failure. A sample of questions drawn the way users ask them would be needed for that.

**Working rule:** Before you count anything, read replies from every variant, grouped by kind, and write down what is wrong with each one. A count can say that a variant fails. Only the replies say how.

## Coding the failures {#coding-the-failures}

Reading becomes counting once each reply has a note and a mode. The drafting model wrote one note per reply, as the one on q-0005 does, and then grouped the notes. Each reply got one mode, its main defect, and a reply with no defect got `ok`. The codes were made by the AI model that drafted this book, as one coder; no second coder checked them, and nobody measured agreement on the codes. The {{out:tally-failure-modes:dev items}} dev items give {{out:tally-failure-modes:replies coded}} replies, {{out:tally-failure-modes:dev items}} from each variant. The codes sit in a data file beside the examples, one entry per reply.

The counts carry the label "coded by the drafting model (one coder; not human labels)", and the label means what it says. This chapter has no agreement figure, and no one else has reproduced the counts. [Chapter 1](measure-before-you-change) made the same point: agreement with your own labels doesn't calibrate a judge. [Chapter 6](calibrate-the-judge) takes that up.

The tally example turns the notes into counts, and it checks the codes first. Each dev item has exactly one code per variant, no code names a mode the file doesn't define, and the file carries the label. Then it prints one row per mode and one column per variant, and one labelled line for each count, which are the numbers the prose below quotes.

[Example: tally-failure-modes](../examples/tally-failure-modes.py)

Read the `ok` row, then the rows under it. The baseline has the most replies with no defect, {{out:tally-failure-modes:ok, baseline}}, and the second-model variant has the fewest, {{out:tally-failure-modes:ok, second-model}}. Over-declining is the largest defect in each variant. In the second-model variant it is more than half of the defects: {{out:tally-failure-modes:over-declining, second-model}} of {{out:tally-failure-modes:defective, second-model}}.

The baseline doesn't escape the worse defects. It gives {{out:tally-failure-modes:wrong-version-answer, baseline}} wrong-version answers, on q-0023 and q-0029, and the unfiltered variant gives the most, {{out:tally-failure-modes:wrong-version-answer, unfiltered}}. Missed refusals come only from the variants, and the baseline has none. Every mode appears at least once. A mode that no variant showed would print as zero, so a reader could see it was looked for.

**Working rule:** Give each reply one note and one mode, and print one labelled line per count, so that every number the prose gives can be checked against the output.

## Over-declining {#over-declining}

An over-declining reply declines an item the docs answer. It is the defect a reader meets first, because a decline looks careful, and it fails the user as surely as a wrong answer does. The terms used here, the decline phrase, the unanswerable item and the variants, are defined in [what the replies look like](#what-the-replies-look-like). The count covers every item the docs answer, version-dependent items included, so for the baseline it is larger than the false refusal rate in [chapter 10](declining-when-the-docs-dont-say), which counts answerable items only. Item q-0004 is the version-dependent case that [chapter 1](measure-before-you-change#declines-in-code) explains in full. All three variants decline it with the same words, so the baseline does this too.

Counting declines has a trap, and it sits in the parser. Item q-0080 is answerable, and the unfiltered variant's reply to it gives two sentences saying the sections don't define the difference, then ends with the decline phrase. The docs answer the question, so the reply is an over-decline. The parser counts a decline only when the phrase is the whole reply, so it reads this one as an answer that cites a section. A reader who searches for the phrase finds it, and a check built on the parser misses it.

The check candidate is that a reply to an item whose reference names a supporting section must not decline, in any words. [Checks in code](checks-in-code) builds checks of that kind. Whether a decline is right on an item the docs don't cover is a judgement, which [chapter 10](declining-when-the-docs-dont-say) takes up.

**Working rule:** Count a decline by what the reply does, not by whether the phrase stands alone, and count over-declining apart from wrong answers, because their checks differ.

## Wrong-version answers {#wrong-version-answers}

A wrong-version answer gives another version's behaviour for the version the question asks about, and it can be fluent and cited while being wrong. In q-0029 the baseline says yes, `sync --apply` creates a missing folder in 1.0, and cites the section on creating folders. The note on the reply says that is the 2.0 behaviour, and that 1.0 has no `--apply` flag at all.

The unfiltered variant does this more often. In q-0021 it says yes to whether `check` gives a nonzero exit status for drift in 1.0, where the baseline and the second-model variant both answer that it does not. The note says the unfiltered reply gave the 2.0 rule for a 1.0 question. Its context holds every version, so the 2.0 rule sits beside the 1.0 one.

Citations don't settle it. In q-0023 the baseline answers yes about a 2.0 result, and it cites the 1.0 section. A check that every citation names a section of the asked version passes that reply. Only the claim, read against the 1.0 reference, shows the error.

**Working rule:** Check each reply's version in two places. Its citations must belong to the asked version, and its claim must match that version's reference. A citation check alone passes an answer that is right about the wrong version.

## Missed refusals {#missed-refusals}

A missed refusal answers an unanswerable item with content the docs don't hold. It is the mode a reader is most likely to believe, because the reply reads like any other answer. The terms used here are defined in [what the replies look like](#what-the-replies-look-like). The dev items show it only in the variants, {{out:tally-failure-modes:missed-refusal, unfiltered}} times in the unfiltered variant and {{out:tally-failure-modes:missed-refusal, second-model}} in the second-model variant, and each is short enough to read whole.

In q-0018 the unfiltered variant says a login token can be sent with a remote template fetch, and cites a section about retries. In q-0034 the second-model variant gives a tip about the lock file, cited to a section that doesn't cover the question. In q-0036 it says `--quiet` suppresses the diff output, citing a section that never mentions the flag. In q-0039 the unfiltered variant answers about `check` when the question asks about `diff`. The baseline declines every one of them.

A code check can require a decline on every unanswerable item, and it would catch each of them. On an answerable item the same fault goes unseen: a reply that cites a real section silent on its claim would pass, because it answers, as an answer is expected there. Reading the claim against the cited section is the work of [chapter 9](grounded-answers) and of [chapter 10](declining-when-the-docs-dont-say).

**Working rule:** Require a decline on every unanswerable item, and read every answer to one against the section it cites before you count it as right.

## From a failure to a check {#from-a-failure-to-a-check}

A failure mode is useful once it has a check candidate, and a candidate has four parts: the mode, the input the check reads, the claim it tests, and what it can't see. A candidate with no stated limit hasn't been thought through. A candidate is also not yet a check. [Checks in code](checks-in-code) builds the checks a program can run, and the judgements go to a judge. The list gives each of the seven failure modes from [coding the failures](#coding-the-failures) its candidate, and names the case that shows it.

- **Over-declining.** A reply to an item whose reference names a supporting section must not decline, in any words. The check can't tell a right decline on an item the docs don't cover from a wrong one, so that judgement goes to [chapter 10](declining-when-the-docs-dont-say).
- **Wrong-version answers.** Every citation must belong to the asked version, and the claim must match that version's reference. The first half is a code check in [checks in code](checks-in-code). The second, which catches q-0023, is version-correctness in [chapter 9](grounded-answers). It can't see a claim the reference doesn't cover.
- **Wrong answers.** The claim must match the reference answer for the asked version, and a reply to an ambiguous item must answer each reading, as [one judge](measure-before-you-change#one-judge) sets out. A judge with a written rubric compares each claim with its reference, as in [chapter 5](a-judge-with-a-rubric). Its test case is q-0005, where the baseline says 2.0 never reads sablefile.lock and the reference says it falls back to it. For ambiguous items the rubric must put both readings in the reference, as q-0048 needs: the unfiltered variant says yes and the second-model variant says no, and each is wrong about one reading. The judge can be wrong too, which [chapter 6](calibrate-the-judge) measures.
- **Missed refusals.** Every reply to an unanswerable item declines, or a reader checks its citation against the section it names. The first is a code check. The second is the work of [chapter 9](grounded-answers). The code check reads no section text, so on an answerable item it passes a reply that cites a real section silent on its claim.
- **Incomplete answers.** The reference lists each number, step and reading a right answer needs, and a code check could look for each one in the reply. This book builds no such check. In q-0011 the baseline says the retry count is fixed and that no flag changes it, but never gives the number. The unfiltered variant does give it, so a check for the reference's number would fail the baseline's reply. Its limit: a number can appear in the reply without being the answer.
- **Citation problems.** Every citation must be one of the item's supporting sections. In q-0057 the baseline is right that `check` doesn't see changes on a remote server, but it cites a section the item doesn't list as supporting, so the citation is unlisted. A code check against that list catches it. Its limit: a listed section can still fail to support the claim, which takes a reader, as [checks in code](checks-in-code) explains.
- **Malformed replies.** A check on the reply's shape, against the format the prompt asks for, catches a reply that comes out in the wrong order. The second-model reply to q-0030 puts its citation first and garbles its sentence, though its answer is right. Its limit: shape says nothing about the answer, so a reply can pass the shape check and still be wrong. The format checks in [checks in code](checks-in-code) build it.

Each candidate in the list names the reply it would have caught, and that is its first test. If a candidate doesn't flag the reply it was written for, it isn't yet a check for the mode.

Build the code checks first. They run in seconds and need no model call, so they can run on every change. A judge costs a model call for each reply and needs its own calibration, so it goes to the modes that a reference and a citation can't settle. Wrong answers need one for the claim. Wrong-version answers need one only for the part that reads a claim against its reference, and missed refusals need one only for the part that reads a claim against the section it cites.

In production the modes don't arrive labelled. A user reports a wrong reply, and the first question is which mode it is, because a check written for the wrong mode passes the reply that failed. When no mode fits, read the failing replies again, code them, add a mode and write its check. This is why the chapter reads and codes the replies before it counts anything.

The list isn't closed: the held-out items and any later variant will show modes these items don't, and each will need its own note and its own candidate.

The chapter made these decisions:

- One coder made the codes: the drafting model. They are labelled as such, and no agreement is measured.
- The dev items are the only items read here; the held-out decline counts appear in chapter 10.
- The baseline's replies are counted with the variants, so its {{out:tally-failure-modes:wrong-version-answer, baseline}} wrong-version answers are reported as such.

**Working rule:** Code the replies by their main defect before you choose a check, and write each check for one mode. A check built from the failures you expected tests for those failures, and it passes the ones you didn't expect.

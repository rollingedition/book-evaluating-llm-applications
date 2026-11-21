---
chapter_id: grounded-answers
---

# Check that answers rest on the cited docs, in the asked version

By the end of this chapter you can count whether an answer's citations support what it says, whether every claim in it rests on the sections the assistant was given, whether it is right for the version the reader asked about, and whether retrieval reached the right section on the way.

A correct answer can still be a poor one. The assistant in this book answers questions about sablefile from its documentation, and a reply passes when it matches the reference answer for the version the question asks about. A reply can pass that test and still cite a section that doesn't say what its sentence says, add a detail that no section gives, or take its facts from another version of the docs. A pass rate sees none of these. A reader who checks the citation beside a claim can, which is why the assistant is asked to cite at all.

Four checks sit beside the pass rate, and each has its own count over its own denominator. Citation accuracy asks whether each citation names a section the item lists as supporting. Faithfulness asks whether each claim is in the sections the assistant was shown. Version-correctness asks whether the answer fits the asked version. Outcome against path asks whether a pass came with its section in hand, and whether a fail had it. Citation accuracy and faithfulness leave declines out, since a decline makes no claim to check. Version-correctness and the retrieval table keep the declines, as the pass rate does, and each prints how many declines it holds.

## What grounded means here {#what-grounded-means}

An answer is grounded when a reader who follows its citations finds the claim where the citation says it is, in the version they asked about. Three things have to hold for that. The citation must exist in that version and support the sentence it is attached to. Every claim in the answer must follow from the sections the assistant read. And the answer must be right for that version, not merely right for some other version that uses the same words.

Take a reader who asks how long a remote fetch waits before it gives up. Suppose the reply gives a plausible answer and cites the section on fetching remote templates, but that section never says how long the wait is. A reader would take the reply as grounded, and the citation looks right. The reader who opens the section finds nothing to support the number. A pass rate would count that reply as correct if the number happened to match the reference. Faithfulness is the check that reads the sections, through a judge. The citation check reads only IDs, and says so.

These failures are different, and each needs its own count. A reply can have a supporting citation and still state a detail the section leaves out, so citation accuracy does not show faithfulness. A reply can be faithful to a section of one version and wrong for another, so faithfulness does not show version-correctness. And a reply can be right and well cited while the retrieval step never reached the section it leans on. Outcome against path exists to find that case.

**Working rule:** Give each check its own count over its own denominator, and treat a pass as the start of the reading, not the end of it.

## Citation accuracy {#citation-accuracy}

A citation is a claim about the docs: this section, in this version, supports the sentence it is attached to. Like any claim, it can be wrong. The section can exist and say something else. It can belong to another version. Or the reply can cite a section the item doesn't list. The Primer covers the sentence-level check, [checking what a cited item supports](https://rollingedition.com/primer-on-search-relevance/s/check-citation-support), and [checking citations against context](https://rollingedition.com/primer-on-search-relevance/s/check-citations-against-context) covers the context a model was given. This book's check is simpler, and [citation checks](checks-in-code#citation-checks) in chapter 4 gives its four outcomes. It matches each cited ID against the item's list of supporting sections for the asked version. It never reads the section, so it says nothing about the sentence.

The code prints two counts from the same replies. The citation rate counts every citation in answered items that is supported. The item rate counts an answered item once if at least one of its citations is supported, so one good citation carries the item. A citation to a section of the asked version that the item does not list is printed as unlisted. That section may well be right, so the check does not call it wrong, and it does not open the section to find out. Reading an unlisted citation is a hand decision. If the section supports the sentence, the item's list of supporting sections is incomplete, and the test set's owner should add it. If it does not, the citation is wrong, and the reply should be read as a failed citation.

Run it on both splits, and read the item line before the citation line.

[Example: citation-accuracy-counts](../examples/citation-accuracy-counts.py)

On dev, the item rate is {{out:citation-accuracy-counts:dev answered items citing a supporting section of the asked version}}.

On dev, {{out:citation-accuracy-counts:dev answered items with no supported citation}} answered items have no supported citation, and the output names them. On held-out, the count is {{out:citation-accuracy-counts:held-out answered items with no supported citation}}.

The citation rate on dev is {{out:citation-accuracy-counts:dev citations that are supported}}. The unlisted citations on dev are {{out:citation-accuracy-counts:dev citations that are unlisted}}, which the output reports and does not count as errors.

On held-out, the item rate is {{out:citation-accuracy-counts:held-out answered items citing a supporting section of the asked version}}, and the citation rate is {{out:citation-accuracy-counts:held-out citations that are supported}}. Held-out has only {{out:citation-accuracy-counts:held-out answered items}} answered items, so one item moves its rate a long way. A difference between the splits would need an interval before anyone called it real, and [intervals and sample size](intervals-and-sample-size) explains how to build one.

The citations that are wrong-version or missing are the ones that would be wrong for a reason the check can name. On dev, they are {{out:citation-accuracy-counts:dev citations that are wrong-version or missing}}. On held-out, they are {{out:citation-accuracy-counts:held-out citations that are wrong-version or missing}}. So the citation rates fall short of 100% because of unlisted citations, and a person has to read those.

The two rates can diverge for a simple reason. An item with one supported citation and one unlisted citation counts in the item rate and lowers the citation rate. Reading both shows whether the misses sit in whole items or in single citations inside items that otherwise hold up.

The idea behind the check has been studied outside this book. Gao and colleagues (2023), at EMNLP 2023 and [on arXiv](https://arxiv.org/abs/2305.14627), built a benchmark for citations in generated answers, and reported that many answers from strong models were not fully supported by their cited passages. Their setup was not this book's, so no number is carried over from them. The paper is cited for the idea.

**Working rule:** Read the item rate and the citation rate together, and read each unlisted citation before you change a prompt. An unlisted citation is a question for the docs, not an error to count.

## Faithfulness {#faithfulness}

Citation accuracy runs without a model, but its counts say how many citations name a listed section, not whether each sentence holds. Faithfulness is the next question, and it is the one that catches claims with no citation at all.

Citation accuracy checks only the sentences that carry a citation. A claim the reply makes without one escapes it, and so does a claim that a cited section supports only in part. Faithfulness asks a wider question: does every claim in the answer follow from the sections the assistant was shown?

Ragas (Es and colleagues, 2023, also a [preprint](https://arxiv.org/abs/2309.15217)) scores faithfulness as the share of an answer's statements that the context supports. It splits the answer into statements and checks each one. This book asks one question per answer instead. The faithfulness prompt in `lib/prompts.py` gives the judge the sections and the answer. The judge reads the answer claim by claim, and writes `VERDICT: SUPPORTED` on its first line only if every claim holds. Otherwise it writes `VERDICT: UNSUPPORTED`, then one sentence of reason.

The difference from citation accuracy shows up in the middle of an answer. Suppose a reply has two sentences. The first carries a citation to a section that supports it, and the second has none, because it adds a detail the section leaves out. Citation accuracy scores the first sentence and says nothing about the second. Faithfulness reads the whole answer, so it can mark the reply unsupported on the second sentence alone. Neither check replaces the other, which is why both are kept.

Nobody has checked this judge's verdicts against a person's, so every faithfulness rate here is uncalibrated. The judge is also the assistant's own model, Qwen3-4B-Instruct-2507, so it grades answers that model wrote. [Self-preference](when-the-judge-stops-being-reliable#self-preference) explains why that matters, and why this book cannot test it. Calibrating the judge would need human ratings of these replies, which this book doesn't have. [Calibrate the judge](calibrate-the-judge) describes the method, which compares the judge with ratings made by hand. Because these rates are not calibrated, there is nothing for the [transfer assumption](calibrate-the-judge#transfer-assumption) to carry over, and the limits in [where to stop](when-the-judge-stops-being-reliable#where-to-stop) apply to them in full.

[Example: faithfulness-rate](../examples/faithfulness-rate.py)

The example takes the baseline's answered items, leaves out the declines, and asks the judge about each one. It prints a rate only over verdicts it can read. A reply that is neither SUPPORTED nor UNSUPPORTED is printed by item and left out of the denominator. It is never counted as a failure, as [verdict first](a-judge-with-a-rubric#verdict-first) explains.

The uncalibrated faithfulness rate on dev is {{out:faithfulness-rate:dev faithfulness rate}}. Its interval is {{out:faithfulness-rate:dev 95% interval of the faithfulness rate}}. The top of that interval sits on the upper boundary of the rate scale, because a bootstrap cannot resample past it. The interval is still wide, which is the honest reading of {{out:faithfulness-rate:dev answered items}} answered items.

The uncalibrated faithfulness rate on held-out is {{out:faithfulness-rate:held-out faithfulness rate}}. Its printed interval is {{out:faithfulness-rate:held-out 95% interval of the faithfulness rate}}, but that is not an interval. The output says the bootstrap is degenerate: {{out:faithfulness-rate:held-out bootstrap interval is degenerate}}. A resample of items that all pass can only return the same rate, so the bootstrap says nothing about where the rate lies.

The exact 95% lower bound is {{out:faithfulness-rate:held-out exact 95% lower bound for 25 of 25}}. Below that true rate, all of the held-out replies passing would happen with probability under 2.5%. The bound is 0.025 to the power of one over n. It shows that the judge passed these replies, on a split too small to show where the rate lies. Do not read the held-out figure as a finding that the assistant is faithful.

The two checks print their own lists. The citation output names the items with no supported citation, and the faithfulness output names the first unfaithful dev items. Read the two lists side by side, since this chapter does not assume they name the same items.

**Working rule:** Put "uncalibrated" beside every faithfulness rate, and read the first unfaithful items before you trust the rate. A faithfulness check shows where the judge says a claim is unsupported. It does not show that the judge is right.

## Version-correctness {#version-correctness}

sablefile has three versions of its docs, 1.0, 1.1 and 2.0, and some questions have different answers in each. A reply can be grounded in a section of 1.1 and still be wrong for a reader on 2.0. The book calls these [version-dependent items](#the-twenty-items). Each has a reference answer for the version the reader asked about, and its check asks whether the reply matches that reference. There are {{out:version-correct-answers:baseline dev version-dependent items}} of them on dev and {{out:version-correct-answers:baseline held-out version-dependent items}} on held-out.

Version-dependent items count in the pass rate with every other item, and they also get their own count, beside it. A reply to one of them is judged against the reference for the asked version, so a correct answer for another version fails. That miss would look like a weak assistant if it were only mixed into the general rate. The judged-correct rate is the count for version-dependent items alone, so a version miss shows on its own line, and a team can see whether a change to retrieval moved it. Declines stay in that denominator, as they do in the pass rate, and each split prints how many it holds.

A wrong-version citation is a separate count. It is a citation to a section that exists only in another version. A reply can be right for the asked version and still cite another version's section, and a reader who copies that citation lands in the wrong docs.

This check sees only what the ID tells it. A citation carries an ID, not a version. Most IDs repeat across versions, so a section ID that appears in 1.0, 1.1 and 2.0 looks the same in each. An ID that appears in every version can never be flagged as wrong-version, whichever version the reader asked about. The check can flag a citation only when the asked version lacks its ID and another version has it. The index matters too. A citation to another version is possible only when that version's sections are in the index the reply was built from, so the count has to be read again when the index changes, and a zero from an old index says nothing about a new one.

Two variants are read here. The baseline retrieves from the index of the asked version only. The unfiltered variant retrieves from the indexes of every version together, and shows each section's version in its header, so the model can see where a section comes from. The unfiltered variant is the one that could cite another version, since it is shown them.

[Example: version-correct-answers](../examples/version-correct-answers.py)

Across every version-dependent item, the wrong-version share is {{out:version-correct-answers:baseline all version-dependent items citing a wrong-version section}} for the baseline and {{out:version-correct-answers:unfiltered all version-dependent items citing a wrong-version section}} for the unfiltered variant. A zero says only that the check flagged no ID. The next example shows how few IDs it could have flagged.

[Example: version-check-detail](../examples/version-check-detail.py)

The section IDs found in only one version, counted by version, are {{out:version-check-detail:section IDs found in one version only, by version}}. An ID found in more than one version can still be flagged, but only for a reader on a version that lacks it. For the baseline, the share of citations to version-dependent items that name a shared ID is {{out:version-check-detail:baseline citations to a section ID found in more than one version}}. For the unfiltered variant it is {{out:version-check-detail:unfiltered citations to a section ID found in more than one version}}.

The judged-correct rates differ, though each is read on a small split. On dev, the baseline is judged correct on {{out:version-correct-answers:baseline dev judged correct for the asked version}}.

The unfiltered variant is judged correct on {{out:version-correct-answers:unfiltered dev judged correct for the asked version}}. On these items, the unfiltered variant passes fewer.

On held-out, the baseline is judged correct on {{out:version-correct-answers:baseline held-out judged correct for the asked version}}. The unfiltered variant has the same rate, but it passes different items. The verdicts go in opposite directions on q-0082 and q-0085, and the other held-out items agree.

Across both variants, the verdicts differ on {{out:version-correct-answers:items where the verdicts differ}} items, out of {{out:version-correct-answers:items with a readable verdict in both variants}} with a readable verdict in each. On dev, {{out:version-check-detail:dev items where the verdicts differ}} of them differ, and on held-out, {{out:version-check-detail:held-out items where the verdicts differ}}. The output lists them by split.

No interval is computed for these differences, and a dev split of this size is small. So this chapter reports the counts and does not call either variant better or worse. The counts say three things: on these items the unfiltered variant passed fewer, no citation was flagged as wrong-version on either variant, and the differing verdicts are the place to read first.

**Working rule:** Read each citation's ID with the version of the answer beside it. A zero from this check means no flagged ID, not no wrong-version citation. Keep version-dependent items in their own count beside the pass rate, so a version miss shows up on its own line.

## Outcome and path {#outcome-and-path}

Outcome is whether a reply passed. Path is what the steps before the reply reached. In this book the path is short: one retrieval, then one reply. Two combinations need both counts. A pass whose supporting section never reached the model came from somewhere else, perhaps the model's own knowledge, and that is a warning even when the verdict is right. A fail with the section retrieved is the case the other checks exist to explain.

Runs with several steps have longer paths. [Agent Harnesses](https://rollingedition.com/agent-harnesses/s/t18-path) counts a task through its path, and that book is the place to read about it. This chapter scores the one step the assistant has.

### The retrieval step {#the-retrieval-step}

Retrieval is BM25 over the sections of the asked version. It is deterministic: the same question gets the same top sections every time. So this step needs no recording. The code computes the top sections for each item from the index, and sets them against the verdict the judge gave the baseline's reply.

Dev items with no supporting section of the asked version are left out of the table. Those are the unanswerable items, since no section of their asked version exists for retrieval to find. Their count is {{out:retrieval-path:dev items with no supporting section of the asked version, left out}}.

[Example: retrieval-path](../examples/retrieval-path.py)

The top k is {{out:retrieval-path:top k}}, read from the baseline's manifest. The table holds {{out:retrieval-path:items in the table}} items, and {{out:retrieval-path:declined items in the table, counted in their cells}} of them are declines. A decline sits in its cell like any other reply, since the judge gave it a verdict. Each cell pairs a verdict with whether a supporting section reached the top k.

| Verdict | Supporting section in the top k | No supporting section in the top k |
| --- | --- | --- |
| PASS | {{out:retrieval-path:right section in the top 3, PASS}} | {{out:retrieval-path:right section not in the top 3, PASS}} |
| FAIL | {{out:retrieval-path:right section in the top 3, FAIL}} | {{out:retrieval-path:right section not in the top 3, FAIL}} |

Read the PASS row first. The cell for passes with the section in the top k holds {{out:retrieval-path:right section in the top 3, PASS}} passes, and the cell for passes without it holds {{out:retrieval-path:right section not in the top 3, PASS}}. That is consistent with passes coming from the docs. It does not show that they did, because the table counts how often two things occur together, not which one caused the other. The count of passes is also a check on the reference. A pass with no section retrieved can come from a reply that repeats a common fact, or from a reference answer a reader could guess, and the table cannot say which. Reading those items can.

The FAIL row is where the other checks come in. Of the failures with the section in the top k, {{out:fail-with-section:right section in the top 3, FAIL, declined}} are declines, and the rest are answers. [Declining when the docs don't say](declining-when-the-docs-dont-say) covers what a decline means when the docs hold the answer. The example below splits the cell.

[Example: fail-with-section](../examples/fail-with-section.py)

Of the answered failures, {{out:fail-with-section:answered FAIL with the section, citing a listed section}} cite a section the item lists. The faithfulness judge passes {{out:fail-with-section:answered FAIL with the section, faithfulness SUPPORTED}} of them and marks {{out:fail-with-section:answered FAIL with the section, faithfulness UNSUPPORTED}} unsupported, which is q-0029. The counts here do not show whether the wrong refusals, the version misses or the answer judge's errors account for the rest. Reading the replies can.

One verdict reads PARTIAL, not PASS or FAIL. The judge's verdict on q-0043 is PARTIAL, so the table leaves it out. An unreadable verdict is never counted as a fail.

**Working rule:** Treat retrieval as a gate on passes and as a lead on fails. A pass without the supporting section needs an explanation, and a fail with it points at the reply.

### Where agent harnesses picks up {#where-agent-harnesses-picks-up}

When a task takes several steps, each one may call a tool and change what the next step sees. The outcome can pass while a middle step went wrong, so the count has to be taken over the whole path. This book scores one retrieval and one reply, so its path count is a yes or no per item. The section on a task counted through a path in [Agent Harnesses](https://rollingedition.com/agent-harnesses/s/t18-path) covers how to score runs of that kind, and this chapter does not repeat it.

**Working rule:** In this book the path is one retrieval and one reply, so read the retrieval count beside the verdict for each item.

## Retrieval quality belongs to another book {#retrieval-quality}

How well retrieval orders the sections, and how much of the context it fills, is a question about ranking, and it belongs to *A Primer on Search Relevance*. Its [choosing a ranking metric](https://rollingedition.com/primer-on-search-relevance/s/choose-a-ranking-metric) section covers recall at k, mean reciprocal rank and nDCG, and how to choose among them. [Measuring the context](https://rollingedition.com/primer-on-search-relevance/s/measure-the-context) covers the context a model is given. Read both before you pick a metric for this assistant.

The retrieval-path count asks one question of each item: is a supporting section of the asked version in the top k? It returns yes or no, so it is not a ranking metric. It cannot say how far down the list that section sits, and that is what a ranking metric is for. Its k is read from the baseline's manifest and is not chosen in this chapter, so a change to k moves the table, and the table has to be read again.

Taken together, the four checks say that a pass rate on this assistant hides three different ways of being wrong. The reply can cite the wrong thing, state what no section says, or answer for the wrong version. Each one needs its own count, its own denominator and its own word for what it found. The decisions that follow from the results are these:

- Each reply is checked for citations, faithfulness and version, and each check keeps its own count.
- Every faithfulness rate is printed as uncalibrated until someone checks the judge against people.
- Version-dependent items keep their own count beside the pass rate, and their own version check.
- Retrieval is a gate on passes and a lead on fails. A pass whose section was not retrieved is read before it is counted as grounded.

**Working rule:** Before you call a reply grounded, read its citation, its claims and its version, and read the retrieval that came before it.

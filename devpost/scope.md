---
doc: scope
status: draft
---

# CrystalForge

A conversational workspace for preparing experimental molecular-crystal CIFs in
the existing MatterVis terminal and browser applications.

## The Unique Kernel

One evidence-backed inspect–repair–validate loop connects user intent, real MCK
operations and native structure views. Completion depends on the exported
structures passing the declared checks, not on reassuring chat text.

## Who It's For

A wet-lab researcher with experimental CIFs containing disorder or missing
hydrogens, currently doing repeated manual preparation before computational work.

## The Core Loop

Load inputs, describe preparation, inspect findings, answer consequential scientific
questions, review executed changes and checks, then retrieve CIFs and records.
Repeat with another input set using the same workflow in either frontend.

## Inspiration & Identity

Reuse [MatterVis](https://github.com/SchrodingersCattt/MatterVis)'s actual UI/TUI
and [MolCrysKit](https://github.com/SchrodingersCattt/MolCrysKit)'s chemistry.
Structure left, optional Forge Chat right. White/light-gray web surfaces with
dark gray, navy, dark teal and crimson accents; Arial prose and Consolas technical
text where supported. Terminal font is user-controlled.
[Learn ShareAI](https://learn.shareai.run/zh/) supplies agent-loop concepts, not
copied shell-agent code.

## Why This Matters to the Learner

The stated project aim is a real molecular-crystal preparation workflow and task
demonstration building on existing tools. Personal motivation, experience and
learning preferences have not been recorded; none is inferred here.

## What "Working" Looks Like

In both native frontends, a researcher follows a batch from input through explicit
decisions and real repairs to reloaded, checked CIFs with traceable records. An
unresolved input visibly prevents whole-batch completion. Seeing chat findings
beside the actual native structure workspace demonstrates the central idea.
A proposed 100-input comparison is not yet a benchmark or acceptance measurement.

## The POC Boundary

Experimental CIFs; read-only inspection followed by missing-H completion and
disorder handling; current MCK criteria; local task persistence and recovery;
strict export/reload; equivalent core workflow in real MatterVis UI/TUI.
Slice 1 delivers only optional chat and real read-only inspection.

## Later

Additional scientific operations and richer versioned viewer commands/events can
follow verified needs. They must not displace the first preparation workflow.

## Explicitly Cut

- New viewers or chemistry engines: reuse the existing applications and MCK.
- Calculation input decks, energy optimization and compute submission: outside
  starting-structure preparation.
- Arbitrary shell execution, autonomous agent teams and scheduling: unnecessary
  authority and complexity for this shared local workflow.
- Hosted accounts and collaboration: not needed for the local proof of concept.

## Approval Evidence

On 2026-09-29 the user said “Start implementation” after the complete 12-section
plan, including actual frontend reuse. This artifact remains draft for main's
consolidation review; no additional user approval or completed build is invented.
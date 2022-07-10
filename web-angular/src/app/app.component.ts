import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface VerbPair {
  es: string;
  gl: string;
}

interface Alignment {
  es: string;
  gl: string;
  tense: string;
  person: string;
  pairEs: string;
  pairGl: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  pairSearch = '';
  alignmentSearch = '';
  selectedPair: VerbPair | null = null;
  selectedTense = 'ALL';
  selectedPerson = 'ALL';

  loadingPairs = true;
  loadingAlignments = true;

  pairs: VerbPair[] = [];
  filteredPairs: VerbPair[] = [];

  alignments: Alignment[] = [];
  filteredAlignments: Alignment[] = [];

  tenseOptions: string[] = [];
  personOptions: string[] = [];

  errorMessage = '';

  readonly maxRows = 300;
  readonly maxQueryLength = 120;

  constructor(private readonly http: HttpClient) { }

  ngOnInit(): void {
    this.loadPairs();
    this.loadAlignments();
  }

  private loadPairs(): void {
    this.http
      .get('assets/data/verbos_relacionados.tsv', { responseType: 'text' })
      .subscribe({
        next: (raw) => {
          this.pairs = this.parsePairs(raw);
          this.filteredPairs = [...this.pairs];
          this.loadingPairs = false;
        },
        error: () => {
          this.loadingPairs = false;
          this.errorMessage =
            'No se pudo cargar el listado de pares. Comprueba assets/data/verbos_relacionados.tsv';
        }
      });
  }

  private loadAlignments(): void {
    this.http
      .get('assets/data/alineaciones_completas.tsv', { responseType: 'text' })
      .subscribe({
        next: (raw) => {
          this.alignments = this.parseAlignments(raw);
          this.tenseOptions = this.buildOptions(this.alignments.map((x) => x.tense));
          this.personOptions = this.buildOptions(this.alignments.map((x) => x.person));
          this.applyAlignmentFilters();
          this.loadingAlignments = false;
        },
        error: () => {
          this.loadingAlignments = false;
          this.alignments = [];
          this.filteredAlignments = [];
        }
      });
  }

  private parsePairs(raw: string): VerbPair[] {
    const seen = new Set<string>();
    const out: VerbPair[] = [];
    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) {
        continue;
      }
      const [es, gl] = line.split('\t');
      if (!es || !gl) {
        continue;
      }
      const key = `${es.toLowerCase()}|${gl.toLowerCase()}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      out.push({ es: es.trim(), gl: gl.trim() });
    }
    return out;
  }

  private parseAlignments(raw: string): Alignment[] {
    const out: Alignment[] = [];
    let currentPairEs = '';
    let currentPairGl = '';

    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) {
        continue;
      }
      const parts = line.split('\t');
      if (parts.length < 4) {
        continue;
      }
      const tense = parts[2].trim();
      const person = parts[3].trim();
      const formEs = parts[0].trim();
      const formGl = parts[1].trim();

      if (tense === 'FN-FN' && person === 'Inf') {
        currentPairEs = formEs;
        currentPairGl = formGl;
      }

      out.push({
        es: formEs,
        gl: formGl,
        tense,
        person,
        pairEs: currentPairEs,
        pairGl: currentPairGl
      });
    }
    return out;
  }

  private buildOptions(values: string[]): string[] {
    return [...new Set(values)].sort((a, b) => a.localeCompare(b));
  }

  private normalizeQuery(raw: string): string {
    return raw
      .replace(/[\u0000-\u001F\u007F]/g, ' ')
      .slice(0, this.maxQueryLength)
      .trim()
      .toLowerCase();
  }

  onPairSearchChange(): void {
    const q = this.normalizeQuery(this.pairSearch);
    this.pairSearch = q;

    if (!q) {
      this.filteredPairs = [...this.pairs];
      return;
    }
    this.filteredPairs = this.pairs.filter(
      (p) => p.es.toLowerCase().includes(q) || p.gl.toLowerCase().includes(q)
    );
  }

  choosePair(pair: VerbPair): void {
    this.selectedPair = pair;
    this.applyAlignmentFilters();
  }

  clearPair(): void {
    this.selectedPair = null;
    this.alignmentSearch = '';
    this.applyAlignmentFilters();
  }

  clearAlignmentFilters(): void {
    this.selectedTense = 'ALL';
    this.selectedPerson = 'ALL';
    this.alignmentSearch = '';
    this.applyAlignmentFilters();
  }

  applyAlignmentFilters(): void {
    const query = this.normalizeQuery(this.alignmentSearch);
    this.alignmentSearch = query;
    const terms = query ? query.split(/\s+/).filter(Boolean) : [];

    this.filteredAlignments = this.alignments.filter((row) => {
      if (this.selectedTense !== 'ALL' && row.tense !== this.selectedTense) {
        return false;
      }
      if (this.selectedPerson !== 'ALL' && row.person !== this.selectedPerson) {
        return false;
      }
      if (this.selectedPair) {
        const matchPair =
          row.pairEs === this.selectedPair.es &&
          row.pairGl === this.selectedPair.gl;
        if (!matchPair) {
          return false;
        }
      }

      if (!terms.length) {
        return true;
      }

      const blob = `${row.es} ${row.gl} ${row.tense} ${row.person} ${row.pairEs} ${row.pairGl}`
        .toLowerCase();
      return terms.every((term) => blob.includes(term));
    });
  }

  trackPair(_index: number, pair: VerbPair): string {
    return `${pair.es}|${pair.gl}`;
  }

  trackAlignment(_index: number, row: Alignment): string {
    return `${row.pairEs}|${row.pairGl}|${row.es}|${row.gl}|${row.tense}|${row.person}`;
  }

  get visibleAlignments(): Alignment[] {
    return this.filteredAlignments.slice(0, this.maxRows);
  }

  get hiddenAlignmentCount(): number {
    return Math.max(this.filteredAlignments.length - this.visibleAlignments.length, 0);
  }
}

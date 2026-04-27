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
    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) {
        continue;
      }
      const parts = line.split('\t');
      if (parts.length < 4) {
        continue;
      }
      out.push({
        es: parts[0].trim(),
        gl: parts[1].trim(),
        tense: parts[2].trim(),
        person: parts[3].trim()
      });
    }
    return out;
  }

  private buildOptions(values: string[]): string[] {
    return [...new Set(values)].sort((a, b) => a.localeCompare(b));
  }

  onPairSearchChange(): void {
    const q = this.pairSearch.trim().toLowerCase();
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
    this.alignmentSearch = `${pair.es} ${pair.gl}`;
    this.applyAlignmentFilters();
  }

  clearPair(): void {
    this.selectedPair = null;
    this.alignmentSearch = '';
    this.applyAlignmentFilters();
  }

  applyAlignmentFilters(): void {
    const query = this.alignmentSearch.trim().toLowerCase();
    this.filteredAlignments = this.alignments.filter((row) => {
      if (this.selectedTense !== 'ALL' && row.tense !== this.selectedTense) {
        return false;
      }
      if (this.selectedPerson !== 'ALL' && row.person !== this.selectedPerson) {
        return false;
      }
      if (this.selectedPair) {
        const matchPair =
          row.es.toLowerCase().includes(this.selectedPair.es.toLowerCase()) ||
          row.gl.toLowerCase().includes(this.selectedPair.gl.toLowerCase());
        if (!matchPair) {
          return false;
        }
      }
      if (!query) {
        return true;
      }
      const blob = `${row.es} ${row.gl} ${row.tense} ${row.person}`.toLowerCase();
      return blob.includes(query);
    });
  }

  get visibleAlignments(): Alignment[] {
    return this.filteredAlignments.slice(0, this.maxRows);
  }
}

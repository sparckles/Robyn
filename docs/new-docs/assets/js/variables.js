// global variables;
const doc = document.documentElement;
const toggleId = 'toggle';
const showId = 'show';
const menu = 'menu';
const active = 'active';
const rootURL = window.location.protocol + "//" + window.location.host;
const searchFieldClass = '.search_field';
const searchClass = '.search';

// config defined values
const codeBlockConfig = JSON.parse('{{ partial "functions/getCodeConfig" . }}');
const iconsPath = `{{ partialCached "functions/getIconPath" . }}`;

// defined in i18n / translation files
const quickLinks = '{{ T "quick_links" }}';
const searchResultsLabel = '{{ T "search_results_label" }}';
const shortSearchQuery = '{{ T "short_search_query" }}'
const typeToSearch = '{{ T "type_to_search" }}';
const noMatchesFound = '{{ T "no_matches" }}';

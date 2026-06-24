#!/usr/bin/env node
'use strict';
// Offline Vercel-challenge solver: runs Vercel's own challenge worker + WASM inside
// a Node sandbox to compute the proof-of-work solution for a given token. Does NO
// network itself — the caller (fetch_profile.py, over browser-TLS) supplies the
// worker source and the WASM bytes and submits the result. Prints the
// `x-vercel-challenge-solution` value to stdout.
//
// Env: THM_TOKEN (challenge token), WORKER_JS_PATH (worker source file),
//      WASM_PATH (challenge .wasm file).
const fs = require('node:fs');
const vm = require('node:vm');

const token = process.env.THM_TOKEN;
const workerPath = process.env.WORKER_JS_PATH;
const wasmPath = process.env.WASM_PATH;
const UA = process.env.UA || 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36';
const err = (...a) => console.error('[solve]', ...a);

if (!token || !workerPath || !wasmPath) { err('need THM_TOKEN, WORKER_JS_PATH, WASM_PATH'); process.exit(2); }

const workerSrc = fs.readFileSync(workerPath, 'utf8');
const wasmBytes = fs.readFileSync(wasmPath);

let captured = null;
// fetch stub: serve the local WASM, capture the solution submission, never hit network.
const stubFetch = async (input, init = {}) => {
  let url = typeof input === 'string' ? input : (input && input.url) || '';
  if (url.includes('.wasm')) {
    return new Response(wasmBytes, { status: 200, headers: { 'content-type': 'application/wasm' } });
  }
  if (url.includes('request-challenge')) {
    const h = new Headers(init.headers || (input && input.headers) || {});
    captured = h.get('x-vercel-challenge-solution');
    err('captured solution:', captured);
    return new Response('ok', { status: 200 });
  }
  err('unexpected worker fetch:', url);
  return new Response('', { status: 204 });
};

let onmessageFn = null;
const { port1: workerSide, port2: mainSide } = new MessageChannel();
const self = {
  postMessage: () => {}, addEventListener: () => {}, removeEventListener: () => {},
  set onmessage(fn) { onmessageFn = fn; }, get onmessage() { return onmessageFn; },
  importScripts: () => {}, fetch: stubFetch, WebAssembly, crypto: globalThis.crypto,
  atob, btoa, TextEncoder, TextDecoder, structuredClone, Response, Request, Headers, Blob,
  URL, URLSearchParams, MessageChannel, MessagePort, setTimeout, clearTimeout, setInterval,
  clearInterval, queueMicrotask, Math, Date, JSON, Object, Array, Uint8Array, ArrayBuffer,
  DataView, Promise, Function, console,
  location: { href: 'https://tryhackme.com/.well-known/vercel/security/static/challenge.v2.min.js', origin: 'https://tryhackme.com', protocol: 'https:', host: 'tryhackme.com' },
  navigator: { userAgent: UA, hardwareConcurrency: 8, language: 'en-US', languages: ['en-US', 'en'], platform: 'MacIntel', onLine: true },
  performance: { now: () => Date.now() },
};
self.self = self; self.globalThis = self;
vm.runInContext(workerSrc, vm.createContext(self), { filename: 'challenge.v2.min.js', timeout: 10000 });

mainSide.onmessage = (ev) => {
  const m = ev.data;
  if (m && m.type === 'solve-response') {
    if (captured) { process.stdout.write(captured); process.exit(0); }
    err('solve-response without a captured solution:', JSON.stringify(m).slice(0, 200));
    process.exit(1);
  }
};
if (onmessageFn) onmessageFn({ data: { port: workerSide }, ports: [workerSide] });
setTimeout(() => mainSide.postMessage({ type: 'solve-request', token, version: '2' }), 60);
setTimeout(() => { err('timeout computing solution'); process.exit(1); }, 20000);

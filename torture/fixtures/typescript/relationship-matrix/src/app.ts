import { helper as h, Worker } from "./lib";

export function directAlias(): string {
  return h();
}

export function typedReceiver(worker: Worker): string {
  return worker.processItem();
}

export function construct(): Worker {
  return new Worker();
}

export function stringNoise(): string {
  return "helper() worker.processItem()";
}

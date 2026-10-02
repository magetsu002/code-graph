import { Controller, Get, applyDecorators } from "@nestjs/common";

function WrappedGet(path: string): MethodDecorator {
  return applyDecorators(Get(path));
}

@Controller("users")
export class UserController {
  @Get("direct")
  direct(): string {
    return "direct";
  }

  @WrappedGet("wrapped")
  wrapped(): string {
    return "wrapped";
  }
}

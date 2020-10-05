package com.tooreal.mc.common;

public enum  ApiCode {

    SUCCESS(200,"成功"),
    SERVER_INTERNAL_ERROR(500,"服务器错误"),
    ERROR(503,"服务不可用");

    private Integer code;

    private String msg;

    ApiCode(int code, String msg){
        this.code = code;
        this.msg = msg;
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }
}

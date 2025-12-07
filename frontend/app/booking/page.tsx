"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function BookingLandingPage(): JSX.Element {
    const router = useRouter();

    useEffect(() => {
        router.replace("/");
    }, [router]);

    return <></>;
}

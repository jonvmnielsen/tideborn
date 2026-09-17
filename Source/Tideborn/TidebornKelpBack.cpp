#include "TidebornKelpBack.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornKelpBack::ATidebornKelpBack()
{
	CreatureRole = ETidebornCreatureRole::Tameable;
	DisplayName = FName(TEXT("Kelp-back"));
	MaxHealth = 60.f;
	BaitItemId = FName(TEXT("KelpBait"));
	FeedsNeededToTame = 3;
	BodyColor = FLinearColor(0.15f, 0.45f, 0.55f);
	GetCharacterMovement()->MaxWalkSpeed = 300.f;
	AggroRadius = 0.f;

	// Taller capsule + rounded stack (silhouette ≠ Burr-hound)
	GetCapsuleComponent()->InitCapsuleSize(42.f, 95.f);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* RoundMesh = SphereMesh.Succeeded() ? SphereMesh.Object : (CubeMesh.Succeeded() ? CubeMesh.Object : nullptr);

	if (BodyMesh && RoundMesh)
	{
		BodyMesh->SetStaticMesh(RoundMesh);
		BodyMesh->SetRelativeScale3D(FVector(0.95f, 0.95f, 0.7f));
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -40.f));
	}

	MidMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MidMesh"));
	MidMesh->SetupAttachment(GetRootComponent());
	MidMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	MidMesh->ComponentTags.Add(FName(TEXT("TidebornBody")));
	if (RoundMesh)
	{
		MidMesh->SetStaticMesh(RoundMesh);
		MidMesh->SetRelativeScale3D(FVector(0.75f, 0.75f, 0.55f));
		MidMesh->SetRelativeLocation(FVector(0.f, 0.f, 15.f));
	}

	TopMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TopMesh"));
	TopMesh->SetupAttachment(GetRootComponent());
	TopMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TopMesh->ComponentTags.Add(FName(TEXT("TidebornBody")));
	if (RoundMesh)
	{
		TopMesh->SetStaticMesh(RoundMesh);
		TopMesh->SetRelativeScale3D(FVector(0.5f, 0.5f, 0.4f));
		TopMesh->SetRelativeLocation(FVector(0.f, 0.f, 55.f));
	}
}
